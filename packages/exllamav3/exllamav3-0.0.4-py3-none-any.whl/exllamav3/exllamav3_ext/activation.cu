#include "activation.cuh"
#include <c10/cuda/CUDAGuard.h>
#include <ATen/cuda/CUDAContext.h>
#include <cuda_fp16.h>
#include "util.h"
#include "util.cuh"
#include "compat.cuh"

#define NUM_THREADS 256
#define ACT_SILU 0
#define ACT_GELU 1

__device__ __forceinline__ half _silu(half x)
{
    half one = __float2half(1.0f);
    half neg_x = __hneg(x);
    half e = hexp(neg_x);
    half sum = __hadd(one, e);
    half r = hrcp(sum);
    half result = __hmul(x, r);
    return result;
}

__device__ __forceinline__ half2 _silu(half2 x)
{
    half2 one = __float2half2_rn(1.0f);
    half2 neg_x = __hneg2(x);
    half2 e = h2exp(neg_x);
    half2 sum = __hadd2(one, e);
    half2 r = h2rcp(sum);
    half2 result = __hmul2(x, r);
    return result;
}

__device__ __forceinline__ float _silu(float x)
{
    float e     = __expf(-x);
    float recip = __fdividef(1.0f, 1.0f + e);
    return x * recip;
}

__device__ __forceinline__ half _gelu(half x)
{
    float xf = __half2float(x);
    const float c = 0.797884560803f;  // sqrt(2/Pi)
    float tanh_arg = c * (xf + 0.044715f * xf * xf * xf);
    xf = 0.5f * xf * (1.0 + tanh_opt(tanh_arg));
    return __float2half_rn(xf);
}

__device__ __forceinline__ float _gelu(float x)
{
    const float c = 0.797884560803f;  // sqrt(2/Pi)
    float tanh_arg = c * (x + 0.044715f * x * x * x);
    x = 0.5f * x * (1.0 + tanh_opt(tanh_arg));
    return x;
}

__device__ __forceinline__ half2 _gelu(half2 x)
{
    return __halves2half2(_gelu(__low2half(x)), _gelu(__high2half(x)));
}

template <int activation_type>
__global__ __launch_bounds__(NUM_THREADS)
void act_mul_kernel_h
(
    const half* __restrict__ x,
    const half* __restrict__ y,
    half* __restrict__ z,
    int numel
)
{
    int idx = (blockIdx.x * NUM_THREADS + threadIdx.x);
    if (idx >= numel / 2) return;

    half2 x2 = ((const half2*) x)[idx];
    half2 y2 = ((const half2*) y)[idx];

    if constexpr (activation_type == ACT_SILU)
        x2 = _silu(x2);
    else if constexpr (activation_type == ACT_GELU)
        x2 = _gelu(x2);

    ((half2*) z)[idx] = __hmul2(x2, y2);
}

template <int activation_type>
__global__ __launch_bounds__(NUM_THREADS)
void act_mul_kernel_f
(
    const float* __restrict__ x,
    const float* __restrict__ y,
    half* __restrict__ z,
    int numel
)
{
    int idx = (blockIdx.x * NUM_THREADS + threadIdx.x);
    if (idx >= numel / 2) return;

    float2 x2 = ((const float2*) x)[idx];
    float2 y2 = ((const float2*) y)[idx];

    if constexpr (activation_type == ACT_SILU)
    {
        x2.x = _silu(x2.x);
        x2.y = _silu(x2.y);
    }
    else if constexpr (activation_type == ACT_GELU)
    {
        x2.x = _gelu(x2.x);
        x2.y = _gelu(x2.y);
    }

    x2.x *= y2.x;
    x2.y *= y2.y;
    ((half2*) z)[idx] = __float22half2_rn(x2);
}

// silu(x) * y -> z, in-place if z == x or z == y

void silu_mul
(
    const at::Tensor& x,
    const at::Tensor& y,
    at::Tensor& z
)
{
    const at::cuda::OptionalCUDAGuard device_guard(x.device());
    cudaStream_t stream = at::cuda::getCurrentCUDAStream().stream();

    bool float_input = x.dtype() == at::kFloat;
    if (float_input)
    {
        TORCH_CHECK_DTYPE(y, kFloat);
    }
    else
    {
        TORCH_CHECK_DTYPE(x, kHalf);
        TORCH_CHECK_DTYPE(y, kHalf);
    }

    TORCH_CHECK_DTYPE(z, kHalf);

    int numel = x.numel();
    int blocks = CEIL_DIVIDE(numel, 2 * NUM_THREADS);
    if (float_input)
    {
        act_mul_kernel_f<ACT_SILU><<<blocks, NUM_THREADS, 0, stream>>>
        (
            (const float*) x.data_ptr(),
            (const float*) y.data_ptr(),
            (half*) z.data_ptr(),
            numel
        );
    }
    else
    {
        act_mul_kernel_h<ACT_SILU><<<blocks, NUM_THREADS, 0, stream>>>
        (
            (const half*) x.data_ptr(),
            (const half*) y.data_ptr(),
            (half*) z.data_ptr(),
            numel
        );
    }
}

// silu(x) * y -> z, in-place if z == x or z == y

void gelu_mul
(
    const at::Tensor& x,
    const at::Tensor& y,
    at::Tensor& z
)
{
    const at::cuda::OptionalCUDAGuard device_guard(x.device());
    cudaStream_t stream = at::cuda::getCurrentCUDAStream().stream();

    bool float_input = x.dtype() == at::kFloat;
    if (float_input)
    {
        TORCH_CHECK_DTYPE(y, kFloat);
    }
    else
    {
        TORCH_CHECK_DTYPE(x, kHalf);
        TORCH_CHECK_DTYPE(y, kHalf);
    }

    TORCH_CHECK_DTYPE(z, kHalf);

    int numel = x.numel();
    int blocks = CEIL_DIVIDE(numel, 2 * NUM_THREADS);
    if (float_input)
    {
        act_mul_kernel_f<ACT_GELU><<<blocks, NUM_THREADS, 0, stream>>>
        (
            (const float*) x.data_ptr(),
            (const float*) y.data_ptr(),
            (half*) z.data_ptr(),
            numel
        );
    }
    else
    {
        act_mul_kernel_h<ACT_GELU><<<blocks, NUM_THREADS, 0, stream>>>
        (
            (const half*) x.data_ptr(),
            (const half*) y.data_ptr(),
            (half*) z.data_ptr(),
            numel
        );
    }
}