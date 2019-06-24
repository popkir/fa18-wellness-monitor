/*
package wellness

import dsptools.numbers._
import freechips.rocketchip.amba.axi4stream._
import freechips.rocketchip.config.Parameters
import freechips.rocketchip.diplomacy._


object StandaloneWellness extends App {
  implicit val p: Parameters = Parameters.empty

  chisel3.Driver.execute(args, () => LazyModule(new TLWellnessDataPathBlock(
    filter1Params = FixedPointWellnessParams.filter1Params,
    lineLength1Params = FixedPointWellnessParams.lineLength1Params,
    filterAlphaParams = FixedPointWellnessParams.filterAlphaParams,
    filterBetaParams = FixedPointWellnessParams.filterBetaParams,
    filterGammaParams = FixedPointWellnessParams.filterGammaParams,
    bandpowerParams = FixedPointWellnessParams.bandpowerParams,
    neuralNetsParams = FixedPointWellnessParams.neuralNetsParams,
    configurationMemoryParams = FixedPointWellnessParams.configurationMemoryParams
  ) with dspblocks.TLStandaloneBlock {
    val ioInNode2 = BundleBridgeSource(() => new AXI4StreamBundle(AXI4StreamBundleParameters(n = 8)))

    streamNode := BundleBridgeToAXI4Stream(AXI4StreamMasterParameters()) :=
      ioInNode2

    val in2 = InModuleBody { ioInNode2.makeIO() }
  }).module)
}

*/