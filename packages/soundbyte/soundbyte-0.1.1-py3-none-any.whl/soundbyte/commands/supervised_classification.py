import os
import sys
import json
import torch
import typer
import subprocess
from pathlib import Path
import torch.distributed as dist
from torch.utils.data import DataLoader
from torch.nn.parallel import DistributedDataParallel as DDP


from soundbyte.tools.metrics import Calculator
from soundbyte.chalkboard import ChalkBoardLogger
from soundbyte.data_depot.pytorchspace import Predefined_Dataset
from soundbyte.tools import FileComponentLoader, get_methods_dict
from soundbyte.neural_models.pytorchspace import Predefined_NeuralModels
from soundbyte.penalty_box.pytorchspace import Predefined_LossFunctions
from soundbyte.control_unit.minibatch_logics import Predefined_MBLogics
from soundbyte.control_unit.pytorchspace import Predefined_Optimizers_Schedulers


app = typer.Typer(help="Classification training with automatic GPU detection")


def cleanup_distributed():
    if dist.is_initialized():
        dist.destroy_process_group()


def train_function(config: dict):
    rank = int(os.environ.get('LOCAL_RANK', 0))
    world_size = int(os.environ.get('WORLD_SIZE', 1))
    

    if world_size > 1:
        torch.cuda.set_device(rank)
        DEVICE = torch.device(f'cuda:{rank}')

        if not dist.is_initialized():
            dist.init_process_group(backend='nccl', init_method='env://')
    else:
        DEVICE = torch.device(f'cuda:{config["training"]["gpu"]}')
    
    FileLoader = FileComponentLoader()
    logger = ChalkBoardLogger(experiment_name=config["experiment_name"])
    
    if ".py" in config["dataset"]["name/codefile"]:
        dataset = FileLoader.load_dataset(file_path=config["dataset"]["name/codefile"],
                                          name=config["dataset"].get("class_name", "TrainingDataset"),
                                          **config["dataset"]["parameters"])
    else: 
        dataset = Predefined_Dataset().fetch_dataset(
            dataset_name=config["dataset"]["name/codefile"],
            root=config["dataset"]["download_path"],
            download=config["dataset"]["download"],
            **config["dataset"]["parameters"]
        )

    if ".py" in config["architecture"]["name/codefile"]:
        architecture = FileLoader.load_nnModule(file_path=config["architecture"]["name/codefile"],
                                                name=config["architecture"].get("class_name", "Architecture"),
                                                **config["architecture"]["parameters"])
    else:
        architecture = Predefined_NeuralModels().fetch_model(
            model_name=config["architecture"]["name/codefile"],
            pretrained=config["architecture"].get("pretrained", True),
            **config["architecture"]["parameters"]
        )

    if ".py" in config["loss_function"]["name/codefile"]:
        loss_function = FileLoader.load_nnModule(file_path=config["loss_function"]["name/codefile"],
                                                 name=config["loss_function"].get("class_name", "Loss_Function"),
                                                 **config["loss_function"]["parameters"])
    else:
        loss_function = Predefined_LossFunctions().fetch_loss_function(
            loss_name=config["loss_function"]["name/codefile"],
            **config["loss_function"]["parameters"]
        )
    
    architecture = architecture.to(DEVICE)
    if config["loss_function"]["train"]: loss_function = loss_function.to(DEVICE)
    if world_size > 1:
        architecture = DDP(architecture, device_ids=[rank], find_unused_parameters=True)
        if config["loss_function"]["train"]: loss_function = DDP(loss_function, device_ids=[rank], find_unused_parameters=True)     
        
        
    parameters = list(architecture.parameters())+list(loss_function.parameters() if config["loss_function"]["train"] else [])
    
    
    if (".py" in config["optimizer"]["name/codefile"]) and (".py" in config["scheduler"]["name/codefile"]):
        optimizer, scheduler = FileLoader.load_optimizer_scheduler(model_parameters=parameters,
                                                                   optimizer_file=config["optimizer"]["name/codefile"],
                                                                   optimizer_class=config["optimizer"].get("class_name", "Optimizer"),
                                                                   scheduler_file=config["scheduler"]["name/codefile"],
                                                                   scheduler_class=config["scheduler"].get("class_name", "Scheduler"),
                                                                   optimizer_params=config["optimizer"]["parameters"],
                                                                   scheduler_params=config["scheduler"]["parameters"])
        
    else:
        optim_sched = Predefined_Optimizers_Schedulers(model_parameters=parameters,
                                                       optimizer_name=config["optimizer"]["name/codefile"],
                                                       scheduler_name=config["scheduler"]["name/codefile"],
                                                       optimizer_kwargs=config["optimizer"]["parameters"],
                                                       scheduler_kwargs=config["scheduler"]["parameters"]
                                                       )
        optimizer, scheduler = optim_sched.optimizer, optim_sched.scheduler


    if world_size > 1:
        train_sampler = torch.utils.data.DistributedSampler(dataset=dataset,
                                                            num_replicas=world_size,
                                                            rank=rank,
                                                            shuffle=True,
                                                            drop_last=True)
        train_dataloader = DataLoader(dataset=dataset,
                                      batch_size=config["training"]["batchsize"],
                                      shuffle=False,
                                      sampler=train_sampler,
                                      num_workers=config["training"].get("num_workers", 4),
                                      pin_memory=True,
                                      drop_last=True)
        
        if config["dataset"]["validation"]:
            dataset.set_mode("validation")
            valid_sampler = torch.utils.data.DistributedSampler(dataset=dataset,
                                                                num_replicas=world_size,
                                                                rank=rank,
                                                                shuffle=True,
                                                                drop_last=True)
            valid_dataloader = DataLoader(dataset=dataset,
                                          batch_size=config["training"]["batchsize"],
                                          shuffle=False,
                                          sampler=valid_sampler,
                                          num_workers=config["training"].get("num_workers", 4),
                                          pin_memory=True,
                                          drop_last=True)
        else:
            valid_dataloader = None

    else:
        train_dataloader = DataLoader(dataset=dataset,
                                      batch_size=config["training"]["batchsize"],
                                      shuffle=True,
                                      sampler=None,
                                      num_workers=config["training"].get("num_workers", 4),
                                      pin_memory=True,
                                      drop_last=True)
        if config["dataset"]["validation"]:
            dataset.set_mode("validation")
            valid_dataloader = DataLoader(dataset=dataset,
                                          batch_size=config["training"]["batchsize"],
                                          shuffle=True,
                                          sampler=None,
                                          num_workers=config["training"].get("num_workers", 4),
                                          pin_memory=True,
                                          drop_last=True)
    
    available_minibatch_logics = get_methods_dict(Predefined_MBLogics)
    if ".py" in config["train_minibatch_logic"]["name/codefile"]:
        train_minibatch_logic = FileLoader.load_function(file_path=config["train_minibatch_logic"]["name/codefile"], name="train_minibatch_logic")
    else:        
        if config["train_minibatch_logic"]["name/codefile"] not in list(available_minibatch_logics.keys()):
            raise Exception(
                "{} not available. Available logics are: [{}]".format(config["train_minibatch_logic"]["name/codefile"], list(available_minibatch_logics.keys()))
            )
        train_minibatch_logic = available_minibatch_logics[config["train_minibatch_logic"]["name/codefile"]]
        
    if ".py" in config["valid_minibatch_logic"]["name/codefile"]:
        valid_minibatch_logic = FileLoader.load_function(file_path=config["valid_minibatch_logic"]["name/codefile"], name="valid_minibatch_logic")
    else:
        if config["valid_minibatch_logic"]["name/codefile"] not in list(available_minibatch_logics.keys()):
            raise Exception(
                "{} not available. Available logics are: [{}]".format(config["valid_minibatch_logic"]["name/codefile"], list(available_minibatch_logics.keys()))
            )
        valid_minibatch_logic = available_minibatch_logics[config["valid_minibatch_logic"]["name/codefile"]]
    
        
    available_metrics = get_methods_dict(Calculator)
    if config["training"]["metric"] not in list(available_metrics.keys()):
        raise Exception(
            "{} not available. Available Metrics are: [{}]".format(config["training"]["metric"], list(available_metrics.keys()))
        )

    for epoch in range(1, config['training']['epochs']+1):
        if world_size > 1 and hasattr(train_dataloader.sampler, 'set_epoch'):
            train_dataloader.sampler.set_epoch(epoch)
        
        epoch_loss = 0
        epoch_metric = 0
        
        for tidx, minibatch in enumerate(train_dataloader):
            train_output, train_loss = train_minibatch_logic(minibatch, architecture, loss_function, optimizer, DEVICE)
            train_metric = available_metrics[config["training"]["metric"]](train_output, minibatch[-1])
                        
            if world_size > 1:
                if (tidx%config["training"]["log_minibatchstats_after"]==0) and rank==0:
                    logger.write(
                        "[Training] Epoch/Minibatch: [{}/{}], loss: [{}] {}: [{}]".format(
                            epoch, tidx, train_loss.item(), config["training"]["metric"], train_metric.item()
                        )
                    )
            else:
                if tidx%config["training"]["log_minibatchstats_after"]==0:
                    logger.write(
                        "[Training] Epoch/Minibatch: [{}/{}], loss: [{}] {}: [{}]".format(
                            epoch, tidx, train_loss.item(), config["training"]["metric"], train_metric.item()
                        )
                    )

            epoch_loss += train_loss.item()
            epoch_metric += train_metric.item()
            
        epoch_loss = round(epoch_loss/len(train_dataloader), 2)
        epoch_metric = round(epoch_metric/len(train_dataloader), 2)
        if (rank==0) and (world_size>1):
            logger.write(
                "Training completed for Epoch: [{}], loss: [{}], {}: [{}]".format(
                    epoch, epoch_loss, config["training"]["metric"], epoch_metric
                )
            )
        else:
            logger.write(
                "Training completed for Epoch: [{}], loss: [{}], {}: [{}]".format(
                    epoch, epoch_loss, config["training"]["metric"], epoch_metric
                )
            )
        scheduler.step()
        
        if epoch%config["training"]["validate_after"]==0:

            valid_epoch_loss, valid_epoch_metric = 0, 0

            if valid_dataloader != None:
                if world_size > 1 and hasattr(valid_dataloader.sampler, 'set_epoch'):
                    valid_dataloader.sampler.set_epoch(epoch)
                    
                for vidx, minibatch in enumerate(valid_dataloader):
                    valid_output, valid_loss = valid_minibatch_logic(minibatch, architecture, loss_function, DEVICE)
                    valid_metric = available_metrics[config["training"]["metric"]](valid_output, minibatch[-1])
                
                    if world_size > 1:
                        if (vidx%config["training"]["log_minibatchstats_after"]==0) and rank==0:
                            logger.write(
                                "[Validation] Epoch/Minibatch: [{}/{}], loss: [{}] {}: [{}]".format(
                                    epoch, vidx, valid_loss.item(), config["training"]["metric"], valid_metric.item()
                                )
                            )
                    else:
                        if vidx%config["training"]["log_minibatchstats_after"]==0:
                            logger.write(
                                "[Validation] Epoch/Minibatch: [{}/{}], loss: [{}] {}: [{}]".format(
                                    epoch, vidx, valid_loss.item(), config["training"]["metric"], valid_metric.item()
                                )
                            )

                    valid_epoch_loss += valid_loss.item()
                    valid_epoch_metric += valid_metric.item()
                
                valid_epoch_loss = round(valid_epoch_loss/len(valid_dataloader), 2)
                valid_epoch_metric = round(valid_epoch_metric/len(valid_dataloader), 2)
                if (rank==0) and (world_size>1):
                    logger.write(
                        "Validation completed for Epoch: [{}], loss: [{}], {}: [{}]".format(
                            epoch, valid_epoch_loss, config["training"]["metric"], valid_epoch_metric
                        )
                    )
                else:
                    logger.write(
                        "Validation completed for Epoch: [{}], loss: [{}], {}: [{}]".format(
                            epoch, valid_epoch_loss, config["training"]["metric"], valid_epoch_metric
                        )
                    )
            
            else:
                logger.write("Validation Metric not available")
                    
        if (rank==0) and (world_size>1):
            torch.save(
                {
                    "epoch": epoch,
                    "architecture": architecture.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict(),
                },
                f="epoch_{}_loss_{}_{}_{}_.pth".format(
                    epoch, epoch_loss, config["training"]["metric"], epoch_metric
                )
            )
        else:
            torch.save(
                {
                    "epoch": epoch,
                    "architecture": architecture.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict(),
                },
                f="epoch_{}_loss_{}_{}_{}_.pth".format(
                    epoch, epoch_loss, config["training"]["metric"], epoch_metric
                )
            )    
    if world_size > 1:
        cleanup_distributed()


def launch_torchrun_training(config_path: str, num_gpus: int, nodes: int):
    import tempfile
    import textwrap
    
    script_content = textwrap.dedent(f"""
    import sys
    import os
    import json
    from pathlib import Path
    
    # Add the soundbyte package to Python path
    current_dir = Path(__file__).parent
    while current_dir.name != 'soundbyte' and current_dir.parent != current_dir:
        current_dir = current_dir.parent
    if current_dir.name == 'soundbyte':
        sys.path.insert(0, str(current_dir.parent))
    
    # Import and run the training function
    from soundbyte.commands.supervised_classification import train_function
    
    if __name__ == "__main__":
        config_path = "{config_path}"
        with open(config_path, 'r') as f:
            config = json.load(f)
        train_function(config)
    """)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
        temp_script.write(script_content)
        temp_script_path = temp_script.name
    
    try:
        torchrun_cmd = [
            sys.executable, '-m', 'torch.distributed.run',
            '--standalone',
            f'--nnodes={nodes}',
            f'--nproc_per_node={num_gpus}',
            temp_script_path,
        ]

        env = os.environ.copy()
        env['CUDA_VISIBLE_DEVICES'] = ','.join(str(i) for i in range(num_gpus))
        
        result = subprocess.run(
            torchrun_cmd, 
            env=env, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode != 0:
            print(f"Training failed with exit code: {result.returncode}")
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
        
        return result.returncode
        
    except Exception as _:
        return 1
    finally:
        try:
            os.unlink(temp_script_path)
        except OSError:
            pass

@app.callback(invoke_without_command=True)
def main(
    json_config: Path = typer.Option(..., "--json_config", help="Path to the JSON configuration file")
    ):
    
    with open(json_config, 'r') as f:
        config = json.load(f)
    
    multi_gpu, num_gpus = config["training"]["mgpu"], config["training"]["num_gpus"]
    
    if multi_gpu and num_gpus > 1:
        return_code = launch_torchrun_training(
            str(json_config), 
            num_gpus, 
            nodes=config["training"].get("nodes", 1)
        )
        sys.exit(return_code)
    else:
        train_function(config)


if __name__ == "__main__":
    app()