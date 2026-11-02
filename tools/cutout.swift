// 아이콘 배경 지우기: 맥의 「물체만 오려내기」(Vision)로 배경을 투명하게 하고, 빈 여백을 잘라 정사각형 png로 저장
// 쓰는 법: swiftc -O tools/cutout.swift -o /tmp/cutout && /tmp/cutout 원본이미지 images/{id}-icon.png 400
import Foundation
import Vision
import CoreImage
import AppKit

// usage: cutout <input> <output.png> <size>
let args = CommandLine.arguments
let input = URL(fileURLWithPath: args[1])
let output = URL(fileURLWithPath: args[2])
let size = CGFloat(Double(args[3]) ?? 400)

guard let ci = CIImage(contentsOf: input) else { fatalError("cannot read image") }
let handler = VNImageRequestHandler(ciImage: ci)
let req = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([req])
guard let result = req.results?.first else { fatalError("no foreground found") }
let maskBuf = try result.generateScaledMaskForImage(forInstances: result.allInstances, from: handler)
let mask = CIImage(cvPixelBuffer: maskBuf)

let clear = CIImage(color: .clear).cropped(to: ci.extent)
let cut = ci.applyingFilter("CIBlendWithMask", parameters: [kCIInputBackgroundImageKey: clear, kCIInputMaskImageKey: mask])

let ctx = CIContext()
guard let cg = ctx.createCGImage(cut, from: ci.extent) else { fatalError("render failed") }

// crop to non-transparent bounding box
let w = cg.width, h = cg.height
let rep = NSBitmapImageRep(cgImage: cg)
var minX = w, minY = h, maxX = 0, maxY = 0
for y in 0..<h { for x in 0..<w {
    if let c = rep.colorAt(x: x, y: y), c.alphaComponent > 0.05 {
        if x < minX { minX = x }; if x > maxX { maxX = x }
        if y < minY { minY = y }; if y > maxY { maxY = y }
    }
}}
let bw = maxX - minX + 1, bh = maxY - minY + 1
let side = max(bw, bh)
let pad = Int(Double(side) * 0.04)
let canvas = side + pad * 2
guard let cropped = cg.cropping(to: CGRect(x: minX, y: minY, width: bw, height: bh)) else { fatalError("crop failed") }

let px = Int(size)
let cs = CGColorSpace(name: CGColorSpace.sRGB)!
let g = CGContext(data: nil, width: px, height: px, bitsPerComponent: 8, bytesPerRow: 0, space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
g.interpolationQuality = .high
let scale = size / CGFloat(canvas)
let dw = CGFloat(bw) * scale, dh = CGFloat(bh) * scale
g.draw(cropped, in: CGRect(x: (size - dw) / 2, y: (size - dh) / 2, width: dw, height: dh))
let png = NSBitmapImageRep(cgImage: g.makeImage()!).representation(using: .png, properties: [:])!
try png.write(to: output)
print("ok", bw, bh)
