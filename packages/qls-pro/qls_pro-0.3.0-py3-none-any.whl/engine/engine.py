from typing import List, Dict, Any, Protocol


class ScannerModule(Protocol):
    name: str

    def supported_types(self) -> List[str]:
        ...  # noqa: D401

    def scan(self, target: Any) -> Dict[str, Any]:
        ...


class QuantivirusEngine:
    """Registers & orchestrates scanner modules."""

    def __init__(self) -> None:
        self._modules: List[ScannerModule] = []

    def register(self, module: ScannerModule) -> None:  # noqa: D401
        self._modules.append(module)

    def scan(self, target, scan_type: str) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for module in self._modules:
            if scan_type in module.supported_types():
                results[module.name] = module.scan(target)
        return {
            "target": str(target),
            "scan_type": scan_type,
            "modules": results,
        }
        