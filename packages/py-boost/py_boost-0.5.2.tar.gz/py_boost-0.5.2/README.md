# Py-boost: a research tool for exploring GBDTs

Modern gradient boosting toolkits are very complex and are written in low-level programming languages. As a result,

* It is hard to customize them to suit one’s needs
* New ideas and methods are not easy to implement
* It is difficult to understand how they work

Py-boost is a Python-based gradient boosting library which aims at overcoming the aforementioned problems.

**Authors**: [Anton Vakhrushev](https://kaggle.com/btbpanda), [Leonid Iosipoi](http://iosipoi.com/)
, [Sergey Kupriyanov](https://www.linkedin.com/in/sergeykupriyanov).

## Py-boost Key Features

**Simple**. Py-boost is a simplified gradient boosting library, but it supports all main features and hyperparameters
available in other implementations.

**Fast with GPU**. Despite the fact that Py-boost is written in Python, it works only on GPU and uses Python GPU
libraries such as `CuPy` and `Numba`.

**Efficient inference**. Since v0.4 Py-Boost is able to perform the efficient inference of tree ensembles on GPU.
Moreover, ones your model is trained on GPU, it could be converted to perform the inference on CPU only machine via
converting to the [treelite](https://treelite.readthedocs.io/) format with build-in wrapper (limitation - model should
be trained with `target_splitter='Single'`, which is the default).

**ONNX compatible** Since v0.5 Py-Boost is compatible with ONNX format that allows more options the CPU inference and
model deployment.

**Easy to customize**. Py-boost can be easily customized even if one is not familiar with GPU programming (just replace
np with cp). What can be customized? Almost everything via custom callbacks. Examples: Row/Col sampling strategy,
Training control, Losses/metrics, Multioutput handling strategy, Anything via custom callbacks

## SketchBoost [paper](https://openreview.net/forum?id=WSxarC8t-T)

**Multioutput training**. Current state-of-atr boosting toolkits provide very limited support of multioutput training.
And even if this option is available, training time for such tasks as multiclass/multilabel classification and multitask
regression is quite slow because of the training complexity that scales linearly with the number of outputs. To overcome
the existing limitations we create **SketchBoost** algorithm that uses approximate tree structure search. As we show
in [paper](https://openreview.net/forum?id=WSxarC8t-T) that strategy at least does not lead to performance decrease and
often is able to improve the accuracy

**SketchBoost**. You can try our sketching strategies by using `SketchBoost` class or if you want you can implement your
own and pass to the `GradientBoosting` constructor as `multioutput_sketch` parameter. For the details please
see [Tutorial_2_Advanced_multioutput](https://github.com/AILab-MLTools/Py-Boost/blob/master/tutorials/Tutorial_2_Advanced_multioutput.ipynb)

## Installation

Before installing py-boost via pip you should have cupy installed. You can use:

`pip install -U cupy-cuda110 py-boost`

**Note**: replace with your cuda version! For the details see [this guide](https://docs.cupy.dev/en/stable/install.html)

## Quick tour

Py-boost is easy to use since it has similar to scikit-learn interface. For usage example please see:

* [Tutorial_1_Basics](https://github.com/sb-ai-lab/Py-Boost/blob/master/tutorials/Tutorial_1_Basics.ipynb) for simple
  usage examples
* [Tutorial_2_Advanced_multioutput](https://github.com/sb-ai-lab/Py-Boost/blob/master/tutorials/Tutorial_2_Advanced_multioutput.ipynb)
  for advanced multioutput features
* [Tutorial_3_Custom_features](https://github.com/sb-ai-lab/Py-Boost/blob/master/tutorials/Tutorial_3_Custom_features.ipynb)
  for examples of customization
* [Tutorial_4_Handle_null_targets](https://github.com/sb-ai-lab/Py-Boost/blob/master/tutorials/Tutorial_4_Handle_null_targets.ipynb)
  for the case when multioutput target contains NaNs
* [Tutorial_5_ONNX_inference](https://github.com/sb-ai-lab/Py-Boost/blob/master/tutorials/Tutorial_5_ONNX_inference.ipynb)
  examples of parsing and inference on CPU with ONNX

More examples are coming soon
