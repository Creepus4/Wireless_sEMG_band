#pragma once

#include <memory>
#include <cstring>

struct arrayf {
// Runtime allocated, fixed-size array for single-precision floating point
	private:
	std::unique_ptr<float[]> data;

	public:
	uint32_t size = 0u;

	arrayf() = default;

	arrayf(uint32_t length) : data(std::make_unique<float[]>(length)), size(length) {}

	const float& operator[](uint32_t index) const noexcept {
		return data[index];
	}

	float& operator[](const uint32_t index) noexcept {
		return data[index];
	}

	arrayf(const float* array, uint32_t length) : data(std::make_unique<float[]>(length)), size(length) {
		memcpy(data.get(), array, length * sizeof(float));
	}
};

struct circularBuffer {
// Circular buffer for single precision floating point data
	private:
	std::unique_ptr<float[]> data;
	uint32_t lastElement = 0u;

	public:
	uint32_t bufferSize = 0u;

	circularBuffer() = default;

	circularBuffer(uint32_t length) : data(std::make_unique<float[]>(length)), bufferSize(length) {}

	void push(float value) noexcept {
		data[lastElement] = value;
		lastElement = (lastElement + 1u) % bufferSize;
	}

	const float& operator[](const uint32_t index) const noexcept {
		return data[(lastElement + index) % bufferSize];
	}
};

class WaveletTransform {
	// Only works for data sizes = 2^n, n = integer and integer sampling frequency. Supports 3 data channels or less with single precision floating point data
	public:
	WaveletTransform(const float* frequency, const uint32_t frequencySize, const uint32_t dataSize, const uint32_t samplingFreq);
	~WaveletTransform();
	void writeTransform(float* output, const uint8_t index) noexcept;
	void push(float dataPoint, const uint8_t index) noexcept;

	private:
	circularBuffer data[3]; //Heap allocated smart ptr
	arrayf frequencies; //Heap allocated smart ptr
	float* fftReWaveletMatrix; //Heap allocated
	float* fftImWaveletMatrix; //Heap allocated
	float* reTemp; //Heap allocated
	float* imTemp; //Heap allocated
	float* fftReData; //Heap allocated
	float* fftImData; //Heap allocated

	static constexpr float tau = 6.2831853f;
	uint32_t samplingFrequency;

	void createWavelets() noexcept;;
	void fftData(const circularBuffer& realIn, float* __restrict realOut, float* __restrict imagOut, uint32_t N) noexcept;
	void ifft(float* __restrict real, float* __restrict imag, uint32_t N) noexcept;
	void fftWavelet(float* __restrict realIn, float* __restrict imagIn, float* __restrict realOut, float* __restrict imagOut, uint32_t N) noexcept;
	void fft(float* __restrict realOut, float* __restrict imagOut, uint32_t N, bool inverse = false) noexcept;
};