
package iirFilter

import wellness._
import chisel3.core._
import dsptools.DspTester
import chisel3.core.FixedPoint
import chisel3.util.log2Ceil

class GoldenIIRFilter(taps_A: Seq[Double], taps_B: Seq[Double]) {
    var pseudoRegisters = List.fill(taps_A.length)(0.toDouble)
    var topWire : Double = 0
    var accumulator_A : Double = 0
    var accumulator_B : Double = 0
    
    def poke(value: Double): Double = {
      topWire = value + accumulator_A
      pseudoRegisters = topWire :: pseudoRegisters.take(taps_A.length - 1)

      accumulator_A = 0
      for(i <- taps_A.indices) {
          accumulator_A += taps_A(i) * pseudoRegisters(i)
      }
      topWire = value + accumulator_A

      accumulator_B = topWire * taps_B(0)
      for(i <- 1 until taps_B.length) {
          accumulator_B += taps_B(i) * pseudoRegisters(i-1)
      }
      accumulator_B
  }
}

class IIRFilterTester[T <: chisel3.Data](c: ConstantCoefficientIIRFilter[T], coefficientsA: Seq[Double], coefficientsB: Seq[Double], dataBP: Int) extends DspTester(c) {
  val dataType = c.params.protoData.getClass.getTypeName
  val filter = new GoldenIIRFilter(coefficientsA,coefficientsB)

  for(i <- 0 until 4) {
    var input = scala.util.Random.nextFloat*8
    if ((dataType == "chisel3.core.SInt") || (dataType == "chisel3.core.UInt")) {
      input = scala.util.Random.nextInt(8)
    }

    val goldenModelResult = filter.poke(input)

    poke(c.io.in.bits, input)
    poke(c.io.in.valid, 1)
    //print(s"Input: ${peek(c.io.in.bits)}\n")

    step(1)

    if ((dataType == "chisel3.core.SInt") || (dataType == "chisel3.core.UInt")) {
      expect(c.io.out.bits, goldenModelResult)//, s"i $i, input $input, gm $goldenModelResult, ${peek(c.io.out.bits)}")
    } else {
      val tolerance = 0.1
      fixTolLSBs.withValue(log2Ceil((goldenModelResult.abs*tolerance).toInt+1)+dataBP+1) {
        expect(c.io.out.bits, goldenModelResult)//, s"i $i, input $input, gm $goldenModelResult, ${peek(c.io.out.bits)}")
      }
    }

  }
}

/**
  * Case class holding information needed to run an individual test
  */
case class XYZ(
                // input x, y and z
                xin: Double,
                yin: Double,
                zin: Double,
                // mode
                vectoring: Boolean,
                // optional outputs
                // if None, then don't check the result
                // if Some(...), check that the result matches
                xout: Option[Double] = None,
                yout: Option[Double] = None,
                zout: Option[Double] = None
              )

object UIntIIRFilterTester {
  def apply(params: IIRFilterParams[UInt], coefficients_A: Seq[Double], coefficients_B: Seq[Double], debug: Int): Boolean = {
    if (debug == 1) {
      chisel3.iotesters.Driver.execute(Array("-tbn", "firrtl", "-fiwv"), () => new ConstantCoefficientIIRFilter(params)) {
        c => new IIRFilterTester(c, coefficients_A, coefficients_B, 0)
      }
    } else {
      dsptools.Driver.execute(() => new ConstantCoefficientIIRFilter(params), TestSetup.dspTesterOptions) {
        c => new IIRFilterTester(c, coefficients_A, coefficients_B, 0)
      }
    }
  }
}
object SIntIIRFilterTester {
  def apply(params: IIRFilterParams[SInt], coefficients_A: Seq[Double], coefficients_B: Seq[Double], debug: Int): Boolean = {
    if (debug == 1) {
      chisel3.iotesters.Driver.execute(Array("-tbn", "firrtl", "-fiwv"), () => new ConstantCoefficientIIRFilter(params)) {
        c => new IIRFilterTester(c, coefficients_A, coefficients_B, 0)
      }
    } else {
      dsptools.Driver.execute(() => new ConstantCoefficientIIRFilter(params), TestSetup.dspTesterOptions) {
        c => new IIRFilterTester(c, coefficients_A, coefficients_B, 0)
      }
    }
  }
}
object FixedPointIIRFilterTester {
  def apply(params: IIRFilterParams[FixedPoint], coefficients_A: Seq[Double], coefficients_B: Seq[Double], dataBP: Int, debug: Int): Boolean = {
    if (debug == 1) {
      chisel3.iotesters.Driver.execute(Array("-tbn", "firrtl", "-fiwv"), () => new ConstantCoefficientIIRFilter(params)) {
        c => new IIRFilterTester(c, coefficients_A, coefficients_B, dataBP)
      }
    } else {
      dsptools.Driver.execute(() => new ConstantCoefficientIIRFilter(params), TestSetup.dspTesterOptions) {
        c => new IIRFilterTester(c, coefficients_A, coefficients_B, dataBP)
      }
    }
  }
}

