import ctypes
import numpy as np
import os

_base = os.path.dirname(os.path.abspath(__file__))

# Importing DLL files
fileReader = ctypes.CDLL(os.path.join(_base, 'fileReader.dll'))
waveletTransform = ctypes.CDLL(os.path.join(_base, 'waveletTransform.dll'))

#setup wavelet functions

waveletTransform.createWaveletObjArray.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
waveletTransform.createWaveletObjArray.restype = None


waveletTransform.deleteWaveletObj.argtypes = []
waveletTransform.deleteWaveletObj.restype = None

waveletTransform.pushData.argtypes = [ctypes.c_float, ctypes.c_uint8]
waveletTransform.pushData.restype = None

waveletTransform.transform.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint8]
waveletTransform.transform.restype = None

# Setup fileReader functions
fileReader.writeFile.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint16), ctypes.c_uint32]
fileReader.writeFile.restype = None

fileReader.readFile.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32)]
fileReader.readFile.restype = ctypes.POINTER(ctypes.c_uint16)

fileReader.freeBuffer.argtypes = [ctypes.POINTER(ctypes.c_uint16)]
fileReader.freeBuffer.restype = None

# Wrapper functions

def createWaveletObj(frequencies: np.ndarray, dataSize, samplingFrequency) -> None:
    waveletTransform.createWaveletObjArray(frequencies.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                                            ctypes.c_uint32(frequencies.size), ctypes.c_uint32(dataSize),
                                              ctypes.c_uint32(samplingFrequency))

def deleteObj() -> None:
    waveletTransform.deleteWaveletObj()

def pushData(data, index) -> None:
    waveletTransform.pushData(ctypes.c_float(data), ctypes.c_uint8(index))

def transform(output: np.ndarray, index) -> None:
    waveletTransform.transform(output.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), ctypes.c_uint8(index))

def write(filename: str, data: np.ndarray) -> None:

    data = np.asarray(data, dtype=np.uint16)

    fileReader.writeFile(
        filename.encode("utf-8"),
        data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
        ctypes.c_uint32(data.size)
    )

def read(filename: str) -> np.ndarray:

    length = ctypes.c_uint32()

    ptr = fileReader.readFile(filename.encode("utf-8"), ctypes.byref(length))

    arr = np.ctypeslib.as_array(ptr, shape=(length.value,))
    data = arr.copy()
    fileReader.freeBuffer(ptr)
    return data