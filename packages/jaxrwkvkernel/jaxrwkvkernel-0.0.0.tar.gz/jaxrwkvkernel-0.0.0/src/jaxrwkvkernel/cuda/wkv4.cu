#include <stdio.h>
#include <assert.h>
#include "xla/ffi/api/ffi.h"
#include "cuda_bf16.h"

namespace ffi = xla::ffi;
typedef __nv_bfloat16 bf16;

//----------------------------------------------------------------------------//
//                            Forward pass                                    //
//----------------------------------------------------------------------------//

template <typename F>
__global__ void kernel_forward(const int B, const int T, const int C,
                               const F *__restrict__ const _w, const F *__restrict__ const _u, const F *__restrict__ const _k, const F *__restrict__ const _v,
			       const F *__restrict__ const _s, const uint32_t *__restrict__ const _length, const bool *__restrict__ const _new_starts,
                               F *__restrict__ const _new_s, F *__restrict__ const _y)
{
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    const int _b = idx / C;
    const int _c = idx % C;
    const int _offset = _b * T * C + _c;

    float u = float(_u[_c]);
    float w = float(_w[_c]);
    const F *__restrict__ const k = _k + _offset;
    const F *__restrict__ const v = _v + _offset;
    const F *__restrict__ const s = _s + _b * 3 * C + _c;
    const uint32_t length = _length[_b];
    const bool *__restrict__ const new_starts = _new_starts + _b * T;
    
    F *__restrict__ const new_s = _new_s + _b * 3 * C + _c;
    F *__restrict__ const y = _y + _offset;

    float p = float(s[0]), q = float(s[C]), o = float(s[2*C]);
    float pf = p, qf = q, of = o;
    // p and q are running sums divided by exp(o) (to avoid overflows)
    for (int i = 0; i < T; i++)
    {
        const int ii = i * C;
	const float kk = float(k[ii]);
	const float vv = float(v[ii]);

	
	if (new_starts[i]) {
	  p = 0;
	  q = 0;
	  o = -65500;
	}

        float no = max(o, u + kk);
        float A = expf(o - no);
        float B = expf(u + kk - no);
        y[ii] = F((A * p + B * vv) / (A * q + B));

        no = max(w + o, kk);
        A = exp(w + o - no);
        B = exp(kk - no);
        p = A * p + B * vv;
        q = A * q + B;
        o = no;

	pf = i < length ? p : pf;
	qf = i < length ? q : qf;
	of = i < length ? o : of;
    }

    new_s[0] = F(pf);
    new_s[C] = F(qf);
    new_s[2 * C] = F(of);
    
}


template <typename T, typename Q>
ffi::Error cuda_forward_typed(cudaStream_t stream,
                              T w, T u, T k, T v,
                              T s, ffi::Buffer<ffi::U32> length, ffi::Buffer<ffi::PRED> new_starts,
                              ffi::Result<T> new_s, ffi::Result<T> y,
                              size_t B, size_t T_, size_t C) {
  dim3 threadsPerBlock(min(C, (size_t)32));
  assert(B * C % threadsPerBlock.x == 0);
  dim3 numBlocks(B * C / threadsPerBlock.x);

  kernel_forward<<<numBlocks, threadsPerBlock, 0, stream>>>(
      B, T_, C,
      (const Q *)w.typed_data(), (const Q *)u.typed_data(), (const Q *)k.typed_data(), (const Q *)v.typed_data(),
      (const Q *)s.typed_data(), length.typed_data(), new_starts.typed_data(),
      (Q *)new_s->typed_data(), (Q *)y->typed_data());

  cudaError_t last_error = cudaGetLastError();
  if (last_error != cudaSuccess) {
    return ffi::Error::Internal(std::string("CUDA error: ") + cudaGetErrorString(last_error));
  }

  return ffi::Error::Success();
}



ffi::Error cuda_forward_f32(cudaStream_t stream,
                            ffi::Buffer<ffi::F32> w, ffi::Buffer<ffi::F32> u, ffi::Buffer<ffi::F32> k, ffi::Buffer<ffi::F32> v,
                            ffi::Buffer<ffi::F32> s, ffi::Buffer<ffi::U32> length, ffi::Buffer<ffi::PRED> new_starts,
                            ffi::ResultBuffer<ffi::F32> new_s, ffi::ResultBuffer<ffi::F32> y,
                            size_t B, size_t T, size_t C) {
  return cuda_forward_typed<ffi::Buffer<ffi::F32>, float>(stream, w, u, k, v, s, length, new_starts, new_s, y, B, T, C);
}

XLA_FFI_DEFINE_HANDLER_SYMBOL(
    WKV4FwdF32, cuda_forward_f32,
    ffi::Ffi::Bind()
        .Ctx<ffi::PlatformStream<cudaStream_t>>()  // stream
        .Arg<ffi::Buffer<ffi::F32>>()              // w
        .Arg<ffi::Buffer<ffi::F32>>()              // u
        .Arg<ffi::Buffer<ffi::F32>>()              // k
        .Arg<ffi::Buffer<ffi::F32>>()              // v
        .Arg<ffi::Buffer<ffi::F32>>()              // s
        .Arg<ffi::Buffer<ffi::U32>>()              // length
        .Arg<ffi::Buffer<ffi::PRED>>()              // new_starts
        .Ret<ffi::Buffer<ffi::F32>>()              // new_s
        .Ret<ffi::Buffer<ffi::F32>>()              // y
    .Attr<size_t>("B")
    .Attr<size_t>("T")
    .Attr<size_t>("C"),
    {xla::ffi::Traits::kCmdBufferCompatible});  // cudaGraph enabled



ffi::Error cuda_forward_bf16(cudaStream_t stream,
                            ffi::Buffer<ffi::BF16> w, ffi::Buffer<ffi::BF16> u, ffi::Buffer<ffi::BF16> k, ffi::Buffer<ffi::BF16> v,
                            ffi::Buffer<ffi::BF16> s, ffi::Buffer<ffi::U32> length, ffi::Buffer<ffi::PRED> new_starts,
                            ffi::ResultBuffer<ffi::BF16> new_s, ffi::ResultBuffer<ffi::BF16> y,
                            size_t B, size_t T, size_t C) {
  return cuda_forward_typed<ffi::Buffer<ffi::BF16>, bf16>(stream, w, u, k, v, s, length, new_starts, new_s, y, B, T, C);
}

XLA_FFI_DEFINE_HANDLER_SYMBOL(
    WKV4FwdBF16, cuda_forward_bf16,
    ffi::Ffi::Bind()
        .Ctx<ffi::PlatformStream<cudaStream_t>>()  // stream
        .Arg<ffi::Buffer<ffi::BF16>>()              // w
        .Arg<ffi::Buffer<ffi::BF16>>()              // u
        .Arg<ffi::Buffer<ffi::BF16>>()              // k
        .Arg<ffi::Buffer<ffi::BF16>>()              // v
        .Arg<ffi::Buffer<ffi::BF16>>()              // s
        .Arg<ffi::Buffer<ffi::U32>>()              // length
        .Arg<ffi::Buffer<ffi::PRED>>()              // new_starts
        .Ret<ffi::Buffer<ffi::BF16>>()              // new_s
        .Ret<ffi::Buffer<ffi::BF16>>()              // y
    .Attr<size_t>("B")
    .Attr<size_t>("T")
    .Attr<size_t>("C"),
    {xla::ffi::Traits::kCmdBufferCompatible});  // cudaGraph enabled











//----------------------------------------------------------------------------//
//                            Backward pass                                   //
//----------------------------------------------------------------------------//



template <typename F>
__global__ void kernel_backward(const int B, const int T, const int C,
                                const F *__restrict__ const _w, const F *__restrict__ const _u, const F *__restrict__ const _k, const F *__restrict__ const _v, const F *__restrict__ const _gy,
                                const F *__restrict__ const _s, const uint32_t *__restrict__ const _length, const bool *__restrict__ const _new_starts, const F *__restrict__ const _gs_new,
                                F *__restrict__ const _gw, F *__restrict__ const _gu, F *__restrict__ const _gk, F *__restrict__ const _gv, F *__restrict__ const _gs)
{
    const int idx = blockIdx.x * blockDim.x + threadIdx.x;
    const int _b = idx / C;
    const int _c = idx % C;
    const int _offset = _b * T * C + _c;

    float u = float(_u[_c]);
    float w = float(_w[_c]);
    const F *__restrict__ const k = _k + _offset;
    const F *__restrict__ const v = _v + _offset;
    const F *__restrict__ const s = _s + _b * 3 * C + _c;
    const uint32_t length = _length[_b];
    const bool *__restrict__ const new_starts = _new_starts + _b * T;
    const F *__restrict__ const gy = _gy + _offset;
    const F *__restrict__ const gs_new = _gs_new + _b * 3 * C + _c;

    F *__restrict__ const gk = _gk + _offset;
    F *__restrict__ const gv = _gv + _offset;
    F *__restrict__ const gs = _gs + _b * 3 * C + _c;

    float y[4096], z[4096], zexp[4096];

    float gw = 0, gu = 0;
    float p = float(s[0]), q = float(s[C]);
    float dpdw = 0, dqdw = 0;
    float o = float(s[2*C]);
    for (int i = 0; i < T; i++)
    {
	if (new_starts[i]) {
	    p = 0;
	    q = 0;
	    o = -65500;
	    dpdw = 0;
	    dqdw = 0;
	}
        const int ii = i * C;
        float no = max(o, float(k[ii]) + u);
        float A = exp(o - no);
        float B = exp(float(k[ii]) + u - no);

        float num = A * p + B * float(v[ii]);
        float iden = 1 / (A * q + B);

        y[i] = num * iden;
        z[i] = iden;
        zexp[i] = float(k[ii]) + u - no;

        gw += float(gy[ii]) * (dpdw - dqdw * y[i]) * iden * A;
        gu += float(gy[ii]) * (float(v[ii]) - y[i]) * B * iden;

        no = max(w + o, float(k[ii]));
        A = exp(w + o - no);
        B = exp(float(k[ii]) - no);
        dpdw = A * (p + dpdw);
        dqdw = A * (q + dqdw);
        p = A * p + B * float(v[ii]);
        q = A * q + B;
        o = no;
    }

    float gp = 0, gq = 0;
    o = -65500;
    for (int i = T - 1; i >= 0; i--)
    {
        const int ii = i * C;
        float A = float(gy[ii]) * z[i] * exp(zexp[i]);
        float B = exp(float(k[ii]) + o);
        gk[ii] = F(A * (float(v[ii]) - y[i]) + B * (gp * float(v[ii]) + gq));
        gv[ii] = F(A + B * gp);

        float no = max(w + o, zexp[i] - float(k[ii]) - u);
        A = exp(w + o - no);
        B = float(gy[ii]) * z[i] * exp(zexp[i] - float(k[ii]) - u - no);
        gp = A * gp + B;
        gq = A * gq - B * y[i];
        o = no;
	
	if (new_starts[i]) {
	    gp = 0;
	    gq = 0;
	    o = -65500;
	}
    }

    // Multiply by w because the w -> -exp(w) preprocessing is halfway in the backwards pass, even though it's not in the forward pass
    const int _offsetBC = _b * C + _c;
    _gw[_offsetBC] = F(gw * float(_w[_c]));
    _gu[_offsetBC] = F(gu);

    gs[0] = 0;
    gs[C] = 0;
    gs[2*C] = 0;
}

template <typename T, typename Q>
ffi::Error cuda_backward_typed(cudaStream_t stream,
			       T w, T u, T k, T v, T gy,
			       T s, ffi::Buffer<ffi::U32> length, ffi::Buffer<ffi::PRED> new_starts, T gs_new,
			       ffi::Result<T> gw, ffi::Result<T> gu, ffi::Result<T> gk, ffi::Result<T> gv, ffi::Result<T> gs,
                              size_t B, size_t T_, size_t C) {
  dim3 threadsPerBlock(min(C, (size_t)32));
  assert(B * C % threadsPerBlock.x == 0);
  dim3 numBlocks(B * C / threadsPerBlock.x);

  kernel_backward<<<numBlocks, threadsPerBlock, 0, stream>>>(
      B, T_, C,
      (const Q *)w.typed_data(), (const Q *)u.typed_data(), (const Q *)k.typed_data(), (const Q *)v.typed_data(), (const Q *)gy.typed_data(),
      (const Q *)s.typed_data(), length.typed_data(), new_starts.typed_data(), (const Q *)gs_new.typed_data(),
      (Q *)gw->typed_data(), (Q *)gu->typed_data(), (Q *)gk->typed_data(), (Q *)gv->typed_data(), (Q *)gs->typed_data());
      // (const Q *)w.typed_data(), (const Q *)u.typed_data(), (const Q *)k.typed_data(), (const Q *)v.typed_data(),
      // (const Q *)s.typed_data(), length.typed_data(), new_starts.typed_data(),
      // (Q *)new_s->typed_data(), (Q *)y->typed_data());

  cudaError_t last_error = cudaGetLastError();
  if (last_error != cudaSuccess) {
    return ffi::Error::Internal(std::string("CUDA error: ") + cudaGetErrorString(last_error));
  }

  return ffi::Error::Success();
}

ffi::Error cuda_backward_f32(cudaStream_t stream,
                            ffi::Buffer<ffi::F32> w, ffi::Buffer<ffi::F32> u, ffi::Buffer<ffi::F32> k, ffi::Buffer<ffi::F32> v, ffi::Buffer<ffi::F32> gy,
			    ffi::Buffer<ffi::F32> s, ffi::Buffer<ffi::U32> length, ffi::Buffer<ffi::PRED> new_starts, ffi::Buffer<ffi::F32> gs_new,
                            ffi::ResultBuffer<ffi::F32> gw, ffi::ResultBuffer<ffi::F32> gu, ffi::ResultBuffer<ffi::F32> gk, ffi::ResultBuffer<ffi::F32> gv, ffi::ResultBuffer<ffi::F32> gs,
                            size_t B, size_t T, size_t C) {
  return cuda_backward_typed<ffi::Buffer<ffi::F32>, float>(stream, w, u, k, v, gy, s, length, new_starts, gs_new, gw, gu, gk, gv, gs, B, T, C);
}

XLA_FFI_DEFINE_HANDLER_SYMBOL(
    WKV4BwdF32, cuda_backward_f32,
    ffi::Ffi::Bind()
        .Ctx<ffi::PlatformStream<cudaStream_t>>()  // stream
        .Arg<ffi::Buffer<ffi::F32>>()              // w
        .Arg<ffi::Buffer<ffi::F32>>()              // u
        .Arg<ffi::Buffer<ffi::F32>>()              // k
        .Arg<ffi::Buffer<ffi::F32>>()              // v
        .Arg<ffi::Buffer<ffi::F32>>()              // gy
        .Arg<ffi::Buffer<ffi::F32>>()              // s
        .Arg<ffi::Buffer<ffi::U32>>()              // length
        .Arg<ffi::Buffer<ffi::PRED>>()             // new_starts
        .Arg<ffi::Buffer<ffi::F32>>()              // gs_new
        .Ret<ffi::Buffer<ffi::F32>>()              // gw
        .Ret<ffi::Buffer<ffi::F32>>()              // gu
        .Ret<ffi::Buffer<ffi::F32>>()              // gk
        .Ret<ffi::Buffer<ffi::F32>>()              // gv
        .Ret<ffi::Buffer<ffi::F32>>()              // gs
    .Attr<size_t>("B")
    .Attr<size_t>("T")
    .Attr<size_t>("C"),
    {xla::ffi::Traits::kCmdBufferCompatible});  // cudaGraph enabled


ffi::Error cuda_backward_bf16(cudaStream_t stream,
                            ffi::Buffer<ffi::BF16> w, ffi::Buffer<ffi::BF16> u, ffi::Buffer<ffi::BF16> k, ffi::Buffer<ffi::BF16> v, ffi::Buffer<ffi::BF16> gy,
			    ffi::Buffer<ffi::BF16> s, ffi::Buffer<ffi::U32> length, ffi::Buffer<ffi::PRED> new_starts, ffi::Buffer<ffi::BF16> gs_new,
                            ffi::ResultBuffer<ffi::BF16> gw, ffi::ResultBuffer<ffi::BF16> gu, ffi::ResultBuffer<ffi::BF16> gk, ffi::ResultBuffer<ffi::BF16> gv, ffi::ResultBuffer<ffi::BF16> gs,
                            size_t B, size_t T, size_t C) {
  return cuda_backward_typed<ffi::Buffer<ffi::BF16>, bf16>(stream, w, u, k, v, gy, s, length, new_starts, gs_new, gw, gu, gk, gv, gs, B, T, C);
}

XLA_FFI_DEFINE_HANDLER_SYMBOL(
    WKV4BwdBF16, cuda_backward_bf16,
    ffi::Ffi::Bind()
        .Ctx<ffi::PlatformStream<cudaStream_t>>()  // stream
        .Arg<ffi::Buffer<ffi::BF16>>()              // w
        .Arg<ffi::Buffer<ffi::BF16>>()              // u
        .Arg<ffi::Buffer<ffi::BF16>>()              // k
        .Arg<ffi::Buffer<ffi::BF16>>()              // v
        .Arg<ffi::Buffer<ffi::BF16>>()              // gy
        .Arg<ffi::Buffer<ffi::BF16>>()              // s
        .Arg<ffi::Buffer<ffi::U32>>()              // length
        .Arg<ffi::Buffer<ffi::PRED>>()             // new_starts
        .Arg<ffi::Buffer<ffi::BF16>>()              // gs_new
        .Ret<ffi::Buffer<ffi::BF16>>()              // gw
        .Ret<ffi::Buffer<ffi::BF16>>()              // gu
        .Ret<ffi::Buffer<ffi::BF16>>()              // gk
        .Ret<ffi::Buffer<ffi::BF16>>()              // gv
        .Ret<ffi::Buffer<ffi::BF16>>()              // gs
    .Attr<size_t>("B")
    .Attr<size_t>("T")
    .Attr<size_t>("C"),
    {xla::ffi::Traits::kCmdBufferCompatible});  // cudaGraph enabled






// #include <stdio.h>
// #include <assert.h>

// template <typename F>
// __global__ void kernel_forward(const int B, const int T, const int C,
//                                const F *__restrict__ const _w, const F *__restrict__ const _u, const F *__restrict__ const _k, const F *__restrict__ const _v,
//                                F *__restrict__ const _y)
// {
//     const int idx = blockIdx.x * blockDim.x + threadIdx.x;
//     const int _b = idx / C;
//     const int _c = idx % C;
//     const int _offset = _b * T * C + _c;

//     F u = _u[_c];
//     F w = _w[_c];
//     const F *__restrict__ const k = _k + _offset;
//     const F *__restrict__ const v = _v + _offset;
//     F *__restrict__ const y = _y + _offset;

//     F p = 0, q = 0, o = -65500;
//     // p and q are running sums divided by exp(o) (to avoid overflows)
//     for (int i = 0; i < T; i++)
//     {
//         const int ii = i * C;

//         F no = max(o, u + k[ii]);
//         F A = exp(o - no);
//         F B = exp(u + k[ii] - no);
//         y[ii] = (A * p + B * v[ii]) / (A * q + B);

//         no = max(w + o, k[ii]);
//         A = exp(w + o - no);
//         B = exp(k[ii] - no);
//         p = A * p + B * v[ii];
//         q = A * q + B;
//         o = no;
//     }
// }

// template <typename F>
// __global__ void kernel_backward(const int B, const int T, const int C,
//                                 const F *__restrict__ const _w, const F *__restrict__ const _u, const F *__restrict__ const _k, const F *__restrict__ const _v, const F *__restrict__ const _gy,
//                                 F *__restrict__ const _gw, F *__restrict__ const _gu, F *__restrict__ const _gk, F *__restrict__ const _gv)
// {
//     const int idx = blockIdx.x * blockDim.x + threadIdx.x;
//     const int _b = idx / C;
//     const int _c = idx % C;
//     const int _offset = _b * T * C + _c;

//     F u = _u[_c];
//     F w = _w[_c];
//     const F *__restrict__ const k = _k + _offset;
//     const F *__restrict__ const v = _v + _offset;
//     const F *__restrict__ const gy = _gy + _offset;

//     F *__restrict__ const gk = _gk + _offset;
//     F *__restrict__ const gv = _gv + _offset;

//     F y[4096], z[4096], zexp[4096];

//     F gw = 0, gu = 0;
//     F p = 0, q = 0;
//     F dpdw = 0, dqdw = 0;
//     F o = -65500;
//     for (int i = 0; i < T; i++)
//     {
//         const int ii = i * C;
//         F no = max(o, k[ii] + u);
//         F A = exp(o - no);
//         F B = exp(k[ii] + u - no);

//         F num = A * p + B * v[ii];
//         F iden = 1 / (A * q + B);

//         y[i] = num * iden;
//         z[i] = iden;
//         zexp[i] = k[ii] + u - no;

//         gw += gy[ii] * (dpdw - dqdw * y[i]) * iden * A;
//         gu += gy[ii] * (v[ii] - y[i]) * B * iden;

//         no = max(w + o, k[ii]);
//         A = exp(w + o - no);
//         B = exp(k[ii] - no);
//         dpdw = A * (p + dpdw);
//         dqdw = A * (q + dqdw);
//         p = A * p + B * v[ii];
//         q = A * q + B;
//         o = no;
//     }

//     F gp = 0, gq = 0;
//     o = -65500;
//     for (int i = T - 1; i >= 0; i--)
//     {
//         const int ii = i * C;
//         F A = gy[ii] * z[i] * exp(zexp[i]);
//         F B = exp(k[ii] + o);
//         gk[ii] = A * (v[ii] - y[i]) + B * (gp * v[ii] + gq);
//         gv[ii] = A + B * gp;

//         F no = max(w + o, zexp[i] - k[ii] - u);
//         A = exp(w + o - no);
//         B = gy[ii] * z[i] * exp(zexp[i] - k[ii] - u - no);
//         gp = A * gp + B;
//         gq = A * gq - B * y[i];
//         o = no;
//     }

//     // Multiply by w because the w -> -exp(w) preprocessing is halfway in the backwards pass, even though it's not in the forward pass
//     const int _offsetBC = _b * C + _c;
//     _gw[_offsetBC] += gw * _w[_c];
//     _gu[_offsetBC] += gu;
// }

// void cuda_forward(int B, int T, int C, float *w, float *u, float *k, float *v, float *y)
// {
//     dim3 threadsPerBlock( min(C, 32) );
//     assert(B * C % threadsPerBlock.x == 0);
//     dim3 numBlocks(B * C / threadsPerBlock.x);
//     kernel_forward<<<numBlocks, threadsPerBlock>>>(B, T, C, w, u, k, v, y);
// }

// void cuda_backward(int B, int T, int C, float *w, float *u, float *k, float *v, float *gy, float *gw, float *gu, float *gk, float *gv)
// {
//     dim3 threadsPerBlock( min(C, 32) );
//     assert(B * C % threadsPerBlock.x == 0);
//     dim3 numBlocks(B * C / threadsPerBlock.x);
//     kernel_backward<<<numBlocks, threadsPerBlock>>>(B, T, C, w, u, k, v, gy, gw, gu, gk, gv);
// }
