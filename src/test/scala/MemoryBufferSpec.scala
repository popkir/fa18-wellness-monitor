package memorybuffer

import chisel3._
import chisel3.core.FixedPoint
import org.scalatest.{FlatSpec, Matchers}

class MemoryBufferSpec extends FlatSpec with Matchers {
  behavior of "Memory Buffer"

  it should "UInt Buffer" in {
    val debug = 0

    for(i <- 0 until 15) {
      val params = new MemoryBufferParams[SInt] {
        val protoData = SInt(32.W)
        val nRows = scala.util.Random.nextInt(15) + 1
        val nColumns = scala.util.Random.nextInt(15) + 1
      }

      UIntMemoryBufferTester(params, debug) should be (true)
    }
  }

  it should "FixedPoint Buffer" in {
    val debug = 0

    val dataWidth = 32
    val dataBP = 8

    for(i <- 0 until 15) {
      val params = new MemoryBufferParams[FixedPoint] {
        val protoData = FixedPoint(dataWidth.W,dataBP.BP)
        val nRows = scala.util.Random.nextInt(15) + 1
        val nColumns = scala.util.Random.nextInt(15) + 1
      }

      FixedPointMemoryBufferTester(params, dataBP, debug) should be (true)
    }
  }
}