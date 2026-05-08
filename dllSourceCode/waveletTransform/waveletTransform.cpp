#include "waveletTransform.h"
#include <cmath>

WaveletTransform::WaveletTransform(const float* frequency, const uint32_t frequencySize, const uint32_t dataSize, const uint32_t samplingFreq) : samplingFrequency(samplingFreq) {

	frequencies = arrayf(frequency, frequencySize);

	for (uint32_t i = 0u; i < 3u; i++) {
		data[i] = circularBuffer(dataSize);
	}
	uint32_t doubleDataSize = 2u * dataSize;
	fftReWaveletMatrix = (float*)_aligned_malloc(doubleDataSize * frequencySize * sizeof(float), 64);
	fftImWaveletMatrix = (float*)_aligned_malloc(doubleDataSize * frequencySize * sizeof(float), 64);
	reTemp = (float*)_aligned_malloc(doubleDataSize * sizeof(float), 64);
	imTemp = (float*)_aligned_malloc(doubleDataSize * sizeof(float), 64);
	fftReData = (float*)_aligned_malloc(doubleDataSize * sizeof(float), 64);
	fftImData = (float*)_aligned_malloc(doubleDataSize * sizeof(float), 64);
	std::fill(reTemp, reTemp + doubleDataSize, 0.0f);
	std::fill(imTemp, imTemp + doubleDataSize, 0.0f);

	createWavelets();
}

WaveletTransform::~WaveletTransform() {
	_aligned_free(fftReWaveletMatrix);
	_aligned_free(fftImWaveletMatrix);
	_aligned_free(reTemp);
	_aligned_free(imTemp);
	_aligned_free(fftReData);
	_aligned_free(fftImData);
}

void WaveletTransform::push(float dataPoint, const uint8_t index) noexcept {
	data[index].push(dataPoint);
}

void WaveletTransform::writeTransform(float* output, const uint8_t index) noexcept {
	uint32_t doubleDataSize = 2u * data[index].bufferSize;

	fftData(data[index], fftReData, fftImData, doubleDataSize);

	for(uint32_t i = 0u; i < frequencies.size; i++) {
		for(uint32_t j = 0u; j < doubleDataSize; j++) {
			float dataRe = fftReData[j];
			float dataIm = fftImData[j];
			float waveletRe = fftReWaveletMatrix[i * doubleDataSize + j];
			float waveletIm = fftImWaveletMatrix[i * doubleDataSize + j];

			reTemp[j] = dataRe * waveletRe - (dataIm * waveletIm);
			imTemp[j] = dataRe * waveletIm + dataIm * waveletRe;
		}
		ifft(reTemp, imTemp, doubleDataSize);

		for(uint32_t j = 0u; j < data[index].bufferSize; j++) {
			uint32_t k = j + data[index].bufferSize / 2;
			output[i * data[index].bufferSize + j] = sqrt(reTemp[k] * reTemp[k] + imTemp[k] * imTemp[k]);
		}
	}
}

void WaveletTransform::createWavelets() noexcept {
	float frequency;
	uint32_t doubleDataSize = 2u * data[0].bufferSize;
	int32_t sizeHalf = data[0].bufferSize/2;
	float timeScale = 1.0f / (float)samplingFrequency;

	for(uint32_t i = 0u; i < frequencies.size; i++) {
		frequency = frequencies[i];
		float scale = 0.5f * frequency * frequency;
		float w0 = tau * frequency;

		uint32_t j = 0u;
		for(int32_t k = -sizeHalf; k < sizeHalf; k++) {
			float t = (float)k * timeScale;
			reTemp[j] = frequency * cosf(w0 * t) * expf(-t * t * scale);
			imTemp[j] = frequency * sinf(w0 * t) * expf(-t * t * scale);
			j++;
		}
		fftWavelet(reTemp, imTemp, fftReWaveletMatrix + i * doubleDataSize, fftImWaveletMatrix + i * doubleDataSize, doubleDataSize);
	}
}

void WaveletTransform::fftData(const circularBuffer& realIn, float* __restrict realOut, float* __restrict imagOut, uint32_t N) noexcept {
	uint32_t j = 0u;
	for (uint32_t i = 0u; i < N; ++i) {
		realOut[j] = (i < N/2 ? realIn[i] : 0.0f);
		imagOut[j] = 0.0f;

		uint32_t bit = N >> 1;
		while (j & bit) {
			j ^= bit;
			bit >>= 1;
		}
		j |= bit;
	}
	fft(realOut, imagOut, N);
}

void WaveletTransform::ifft(float* __restrict real, float* __restrict imag, uint32_t N) noexcept {
	uint32_t j = 0u;
	for (uint32_t i = 1u; i < N; ++i) {
		uint32_t bit = N >> 1;
		while (j & bit) {
			j ^= bit;
			bit >>= 1;
		}
		j |= bit;

		if (i < j) {
			std::swap(real[i], real[j]);
			std::swap(imag[i], imag[j]);
		}
	}
	fft(real, imag, N, true);
}

void WaveletTransform::fftWavelet(float* __restrict realIn, float* __restrict imagIn, float* __restrict realOut, float* __restrict imagOut, uint32_t N) noexcept {
	uint32_t j = 0u;
	for (uint32_t i = 0u; i < N; ++i) {
		realOut[j] = realIn[i];
		imagOut[j] = imagIn[i];

		uint32_t bit = N >> 1;
		while (j & bit) {
			j ^= bit;
			bit >>= 1;
		}
		j |= bit;
	}
	fft(realOut, imagOut, N);
}

void WaveletTransform::fft(float* __restrict realOut, float* __restrict imagOut, uint32_t N, bool inverse) noexcept {
	for (uint32_t len = 2u; len <= N; len <<= 1u) {
		uint32_t half = len >> 1u;

		float angle = (inverse ? 1.0f : -1.0f) * tau / float(len);
		float reStepTwiddle = cos(angle);
		float imStepTwiddle = sin(angle);

		for (uint32_t i = 0u; i < N; i += len) {
			float reTwiddle = 1.0f;
			float imTwiddle = 0.0f;

		for (uint32_t j = 0u; j < half; ++j) {
				uint32_t a = i + j;
				uint32_t b = a + half;

				float reUpperButterfly = realOut[a];
				float imUpperButterfly = imagOut[a];

				float reOutput = realOut[b];
				float imOutput = imagOut[b];

				float reLowerButterfly = reOutput * reTwiddle - imOutput * imTwiddle;
				float imLowerButterfly = reOutput * imTwiddle + imOutput * reTwiddle;

				realOut[a] = reUpperButterfly + reLowerButterfly;
				imagOut[a] = imUpperButterfly + imLowerButterfly;
				realOut[b] = reUpperButterfly - reLowerButterfly;
				imagOut[b] = imUpperButterfly - imLowerButterfly;

				float next_reTwiddle = reTwiddle * reStepTwiddle - imTwiddle * imStepTwiddle;
				float next_imTwiddle = reTwiddle * imStepTwiddle + imTwiddle * reStepTwiddle;
				reTwiddle = next_reTwiddle;
				imTwiddle = next_imTwiddle;
			}
		}
	}

	if (inverse) {
		float invN = 1.0f / float(N);
		for (uint32_t i = 0u; i < N; ++i) {
			realOut[i] *= invN;
			imagOut[i] *= invN;
		}
	}
}