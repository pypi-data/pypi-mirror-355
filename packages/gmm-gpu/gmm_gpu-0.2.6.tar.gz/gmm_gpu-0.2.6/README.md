# gmm_gpu

[Documentation](https://mzdravkov.com/docs/gmm_gpu/index.html)

A small library for quick fitting of multiple instances of [Gaussian Mixture Models](https://en.wikipedia.org/wiki/Mixture_model#Gaussian_mixture_model) in parallel on the GPU.

This may be useful if you have a large number of independent small problems and you want to fit a GMM on each one.
You can create a single large 3D tensor (three dimensional matrix) with the data for all your instances (i.e. a batch) and then
send the tensor to the GPU and process the whole batch in parallel. This would work best if all the instances have roughly the same number of points.

If you have a single big problem (one GMM instance with many points) that you want to fit using the GPU, maybe [Pomegranate](https://github.com/jmschrei/pomegranate) would be a better option.

### Installation
```bash
$ pip install gmm-gpu
```

### Example usage:
Import pytorch and the GMM class
```python
>>> from gmm_gpu.gmm import GMM
>>> import torch
```

Generate some test data:
We create a batch of 1000 instances, each
with 200 random points. Half of the points
are sampled from distribution centered at
the origin (0, 0) and the other half from
a distribution centered at (1.5, 1.5).
```python
>>> X1 = torch.randn(1000, 100, 2)
>>> X2 = torch.randn(1000, 100, 2) + torch.tensor([1.5, 1.5])
>>> X = torch.cat([X1, X2], dim=1)
```

Fit the model:
```python
>>> gmm = GMM(n_components=2, device='cuda')
>>> gmm.fit(X)
```

Predict the components:
This will return a matrix with shape (1000, 200) where
each value is the predicted component for the point.
```python
>>> gmm.predict(X)
```
 
### Benchmarking

```python
>>> import torch
>>> from sklearn.mixture import GaussianMixture
>>> from gmm_gpu.gmm import GMM
>>> import timeit
```

We generate 1,000 independent problems. In each problem we have 200 random normally distributed points centered at (0, 0) and another 200 centered at (1.5, 1.5).

```python
>>> origin = torch.randn(1000, 200, 2)
>>> shifted = torch.randn(1000, 200, 2).add(torch.tensor([1.5, 1.5]))
>>> data_torch = torch.cat([origin, shifted], dim=1)
>>> data_numpy = data_torch.numpy()
```

Let's first measure the execution time of scikit-learn's GaussianMixture. We iterate over the 1,000 problems and fit a model on each one. We repeat the measurement 100 times to get more stable results.

```python
>>> timeit.timeit("[GaussianMixture(n_components=2).fit(data_numpy[i]) for i in range(1000)]", globals=globals(), number=100)
1301.5792503219564
```

Then let's test this library, using the CPU to fit the models:

```python
>>> timeit.timeit("GMM(n_components=2, device='cpu').fit(data_torch)", globals=globals(), number=100)
19.02717640507035
```

Finally, let's try to fit the models on the GPU:

```python
>>> data_torch = data_torch.to('cuda')
>>> timeit.timeit("GMM(n_components=2, device='cuda').fit(data_torch)", globals=globals(), number=100)
11.06293786992319
```

* The benchmarking was performed using 8 cores on Intel Xeon E5-2650 v4 and the GPU test used NVIDIA Tesla P100-PCIE-12GB.

