package dwt

import chisel3.Data

trait DWTParams[T <: Data] {
  val protoData: T
  val taps_LPF: Seq[T]
  val taps_HPF: Seq[T]
}