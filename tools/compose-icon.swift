// 앱 아이콘 만들기: 배경이 투명한 그림(오려낸 블루베리)을 흰 정사각형 가운데에 얹어 png로 저장
// 쓰는 법: swiftc -O tools/compose-icon.swift -o /tmp/compose-icon
//          /tmp/compose-icon 오려낸그림.png icon-512.png 512 0.82    ← 마지막 숫자 = 그림이 차지하는 비율
//   - 일반 아이콘(icon-192/512): 0.82 정도
//   - 안드로이드용(maskable, 동그랗게 잘림): 가운데 80% 원 안에 들어가야 하므로 0.62 정도
import Foundation
import AppKit

let a = CommandLine.arguments
guard a.count >= 5, let src = NSImage(contentsOfFile: a[1]),
      let size = Double(a[3]), let ratio = Double(a[4]) else {
  fatalError("usage: compose-icon <input.png> <output.png> <size> <ratio>")
}
let S = CGFloat(size)
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: Int(S), pixelsHigh: Int(S),
                           bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
                           colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSGraphicsContext.current?.imageInterpolation = .high
NSColor.white.setFill()
NSRect(x: 0, y: 0, width: S, height: S).fill()
// 그림을 비율에 맞춰 줄이고 가운데에 놓음 (가로·세로 중 긴 쪽 기준)
let w = src.size.width, h = src.size.height
let scale = S * CGFloat(ratio) / max(w, h)
let dw = w * scale, dh = h * scale
src.draw(in: NSRect(x: (S - dw) / 2, y: (S - dh) / 2, width: dw, height: dh),
         from: .zero, operation: .sourceOver, fraction: 1)
NSGraphicsContext.restoreGraphicsState()
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[2]))
print("ok")
