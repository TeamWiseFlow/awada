import { ScanStatus, log } from "@juzi/wechaty";
import qrTerm from "qrcode-terminal";

/** 扫码登录 */
export const onScan = (qrcode: string, status: ScanStatus) => {
  console.log('🌰🌰🌰 onScan 🌰🌰🌰')
  if (status === ScanStatus.Waiting || status === ScanStatus.Timeout) {
    console.log('waiting || timeout')
    qrTerm.generate(qrcode, { small: true }); // show qrcode on console

    const qrcodeImageUrl = [
      "https://wechaty.js.org/qrcode/",
      encodeURIComponent(qrcode),
    ].join("");

    log.info(
      "StarterBot",
      "onScan: %s(%s) - %s",
      ScanStatus[status],
      status,
      qrcodeImageUrl
    );
  } else {
    log.info("StarterBot", "onScan: %s(%s)", ScanStatus[status], status);
  }
};


