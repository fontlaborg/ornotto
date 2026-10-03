// this_file: runtimes/coreai/Sources/ornotto-coreai/main.swift
import ClefFlash
import CoreAI
import CoreAIKitEmbeddings
import Foundation

func emit(_ value: Any) throws {
    let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data([10]))
}

let args = CommandLine.arguments
if args.count != 4 { fatalError("usage: ornotto-coreai clef|pii <snapshot> <variant>") }
let root = URL(fileURLWithPath: args[2])
let mode = args[1]
let decider: ClefDecider?
let extractor: InformationExtractor?
do {
    if mode == "clef" {
        let decoder = root.appendingPathComponent("gpu-pipelined/clef_flash_decode_\(args[3])_pf64")
        let head = root.appendingPathComponent("gpu-pipelined/clef_flash_head_bucket_fp16w32")
        var options = SpecializationOptions(preferredComputeUnitKind: .gpu)
        options.expectFrequentReshapes = true
        decider = try await ClefDecider(assets: .init(decoderBundle: decoder, head: head,
            table: root.appendingPathComponent("host/lm_head_fp16.bin")), decoderOptions: options,
            headOptions: SpecializationOptions(preferredComputeUnitKind: .gpu))
        extractor = nil
    } else if mode == "pii" {
        extractor = try await InformationExtractor(bundleAt: root.appendingPathComponent("macos"), computeUnits: .gpu)
        decider = nil
    } else { throw NSError(domain: "ornotto", code: 1, userInfo: [NSLocalizedDescriptionKey: "unknown mode"]) }
    try emit(["ready": true])
    while let line = readLine() {
        do {
            let data = Data(line.utf8)
            if let d = decider {
                let result = try await d.decide(request: SystemOneRequest(data: data))
                FileHandle.standardOutput.write(Data((PythonJSON.dumps(result) + "\n").utf8))
            } else if let e = extractor {
                let req = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
                guard let text = req["text"] as? String, let labels = req["labels"] as? [String],
                    !labels.isEmpty, labels.count <= 16, Set(labels).count == labels.count,
                    labels.allSatisfy({ !$0.isEmpty }) else {
                    throw NSError(domain: "ornotto", code: 2, userInfo: [NSLocalizedDescriptionKey: "invalid text or labels (1...16 unique labels)"])
                }
                let threshold = (req["threshold"] as? NSNumber)?.floatValue
                let spans = try await e.extractSpans(from: text, entities: labels, threshold: threshold)
                let records = spans.map { s in ["label": s.label, "text": s.text, "confidence": s.confidence,
                    "start": NSRange(s.range, in: text).location,
                    "end": NSRange(s.range, in: text).location + NSRange(s.range, in: text).length] as [String: Any] }
                try emit(["offset_unit": "utf16", "spans": records, "redacted": InformationExtractor.redact(text, using: spans)])
            }
        } catch { try emit(["error": String(describing: error)]) }
    }
} catch {
    try? emit(["error": String(describing: error)])
    exit(1)
}
