package fft

import chisel3._
import chisel3.core.FixedPoint

import org.scalatest.{FlatSpec, Matchers}


class FFTBufferSpec extends FlatSpec with Matchers {
  behavior of "FFT Buffer"

  it should "convert from stream to parallel (SInt)" in {
    val debug = 0

    for(i <- 0 until 15) {
      val laneCount = scala.util.Random.nextInt(15) + 1

      val params = new FFTBufferParams[SInt] {
        val protoData = SInt(16.W)
        val lanes = laneCount
      }

      SIntFFTBufferTester(params, laneCount, debug) should be (true)
    }
  }

  it should "convert from stream to parallel (FixedPoint)" in {
    val debug = 0

    val dataWidth = 32
    val dataBP = 8

    for(i <- 0 until 15) {
      val laneCount = scala.util.Random.nextInt(15) + 1

      val params = new FFTBufferParams[FixedPoint] {
        val protoData = FixedPoint(dataWidth.W,dataBP.BP)
        val lanes = laneCount
      }

      FixedPointFFTBufferTester(params, laneCount, dataBP, debug) should be (true)
    }
  }

  it should "convert from stream to parallel (Fixed Point)" in {
    val debug = 0

    val dataWidth = 32
    val dataBP = 8

    for(i <- 0 until 15) {
      val laneCount = scala.util.Random.nextInt(15) + 1

      val params = new FFTBufferParams[FixedPoint] {
        val protoData = FixedPoint(dataWidth.W,dataBP.BP)
        val lanes = laneCount
      }

      FixedPointFFTBufferTester(params, laneCount, dataBP, debug) should be (true)
    }
  }
}