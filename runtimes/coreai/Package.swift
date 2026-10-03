// swift-tools-version: 6.1
// this_file: runtimes/coreai/Package.swift
import PackageDescription
let package = Package(
    name: "ornotto-coreai", platforms: [.macOS("27.0")],
    dependencies: [.package(path: ".upstream/ClefFlash"), .package(path: ".upstream/coreai-kit")],
    targets: [.executableTarget(name: "ornotto-coreai", dependencies: [
        .product(name: "ClefFlash", package: "ClefFlash"),
        .product(name: "CoreAIKitEmbeddings", package: "coreai-kit")
    ], linkerSettings: [.linkedFramework("CoreAI")])]
)
