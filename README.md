# ML_pytorch

Repository with basic machine learning algorithms implemented in PyTorch based on my implementation in https://github.com/fcattafesta/hbb/tree/SigBkgDNN/sb_discriminator


# Installation
To create the micromamba environment, you can use the following command:
```bash
micromamba env create -f ML_pytorch_env.yml
pip install -r requirements.txt
```

# Connect to node with a gpu
To connect to a node with a gpu, you can use the following command:
```bash
# connect to a node with a gpu
salloc --account gpu_gres --job-name "InteractiveJob" --cpus-per-task 4 --mem-per-cpu 3000 --time 01:00:00  -p gpu
# activate the environment
micromamba activate ML_pytorch
```

# Examples
To execute a training, evaluate the model on the test set, plot the history and plot the signal/background histograms, you can use the following command:

```bash
python  scripts/train.py -d /work/mmalucch/out_hh4b/out_vbf_ggf_dnn_full/ --name name_of_training --eval -o --roc --histos --history --gpus 7 -n 4 -p 50 -b 512 -e 10 -c configs/DNN_config_ggF_VBF.yml
```
