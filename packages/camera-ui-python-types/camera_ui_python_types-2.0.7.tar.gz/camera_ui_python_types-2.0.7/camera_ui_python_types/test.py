import asyncio
import logging
from typing import Any, Optional

from reactivex import Subject

from camera_ui_python_types.hybrid_observer import HybridObservable


async def test_asubscribe_endless_operation():
    # Setup
    subject = Subject[Any]()
    hybrid = HybridObservable(subject)
    processed_values: list[Any] = []
    value_processed = asyncio.Event()

    async def endless_operation(value: Any):
        try:
            processed_values.append(value)
            value_processed.set()  # Signal dass ein Wert verarbeitet wurde
            # Simuliere eine endlose Operation
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"Error in endless operation: {e}")
            raise

    # Subscribe mit der endlosen Operation
    disposable = hybrid.asubscribe(on_next=endless_operation)

    try:
        # Sende ersten Wert
        subject.on_next(1)

        # Warte auf Verarbeitung mit Timeout
        try:
            await asyncio.wait_for(value_processed.wait(), timeout=1.0)
        except asyncio.TimeoutError as e:
            raise AssertionError("Timeout beim Warten auf Verarbeitung von Wert 1") from e

        value_processed.clear()  # Reset für nächsten Wert

        # Sende zweiten Wert
        subject.on_next(2)

        # Warte auf Verarbeitung mit Timeout
        try:
            await asyncio.wait_for(value_processed.wait(), timeout=1.0)
        except asyncio.TimeoutError as e:
            raise AssertionError("Timeout beim Warten auf Verarbeitung von Wert 2") from e

        # Überprüfe, ob beide Werte verarbeitet wurden
        assert processed_values == [1, 2], f"Erwartete [1, 2], bekam {processed_values}"

        # Cleanup durchführen
        disposable.dispose()
        await asyncio.sleep(0.2)  # Warte auf Cleanup

        # Versuche weitere Werte zu senden
        subject.on_next(3)
        await asyncio.sleep(0.2)

        # Überprüfe, dass keine weiteren Werte verarbeitet wurden
        assert processed_values == [1, 2], (
            f"Nach dispose wurden weitere Werte verarbeitet: {processed_values}"
        )
    finally:
        # Sicherstellen, dass dispose in jedem Fall aufgerufen wird
        disposable.dispose()
        await asyncio.sleep(0.2)  # Warte auf Cleanup


async def test_asubscribe_self_completing_operation():
    # Setup
    subject = Subject[Any]()
    hybrid = HybridObservable(subject)
    processed_values: list[Any] = []
    completion_event = asyncio.Event()
    error_received: Optional[Exception] = None

    async def self_completing_operation(value: Any):
        processed_values.append(value)
        # Simuliere eine Operation, die nach einer gewissen Zeit endet
        await asyncio.sleep(0.1)

    async def on_completed():
        completion_event.set()

    async def on_error(error: Any):
        nonlocal error_received
        error_received = error

    # Subscribe mit der selbstbeendenden Operation
    disposable = hybrid.asubscribe(
        on_next=self_completing_operation, on_completed=on_completed, on_error=on_error
    )

    try:
        # Sende einige Werte
        subject.on_next(1)
        subject.on_next(2)

        # Warte, bis die Operationen abgeschlossen sind
        await asyncio.sleep(0.3)

        # Überprüfe, ob alle Werte verarbeitet wurden
        assert processed_values == [1, 2]

        # Beende den Stream
        subject.on_completed()

        # Warte auf Completion mit Timeout
        try:
            await asyncio.wait_for(completion_event.wait(), timeout=1.0)
        except asyncio.TimeoutError as e:
            raise AssertionError("Completion handler wurde nicht aufgerufen") from e

        # Überprüfe, dass kein Fehler aufgetreten ist
        assert error_received is None, f"Unerwarteter Fehler aufgetreten: {error_received}"
    finally:
        # Cleanup
        disposable.dispose()
        await asyncio.sleep(0.2)  # Warte auf Cleanup


async def test_asubscribe_error_handling():
    # Setup
    subject = Subject[Any]()
    hybrid = HybridObservable(subject)
    error_event = asyncio.Event()
    error_value: Optional[Exception] = None
    processed_values: list[Any] = []

    async def operation_with_error(value: Any):
        processed_values.append(value)
        if value == 2:
            raise ValueError("Test error")
        await asyncio.sleep(0.1)

    async def on_error(error: Any):
        nonlocal error_value
        error_value = error
        error_event.set()

    # Subscribe mit der fehlerwerfenden Operation
    disposable = hybrid.asubscribe(on_next=operation_with_error, on_error=on_error)

    try:
        # Sende ersten Wert und warte auf Verarbeitung
        subject.on_next(1)
        await asyncio.sleep(0.2)

        # Sende Wert der Fehler auslöst
        subject.on_next(2)

        # Warte auf Error Event mit Timeout
        try:
            await asyncio.wait_for(error_event.wait(), timeout=1.0)
        except asyncio.TimeoutError as e:
            raise AssertionError("Error handler wurde nicht aufgerufen") from e

        # Überprüfe Fehlerbehandlung
        assert isinstance(error_value, ValueError), f"Erwartete ValueError, bekam {type(error_value)}"
        assert str(error_value) == "Test error"
        assert processed_values == [1, 2]

        # Versuche weitere Werte zu senden
        subject.on_next(3)
        await asyncio.sleep(0.2)

        # Überprüfe, dass keine weiteren Werte verarbeitet wurden
        assert processed_values == [1, 2], f"Nach Fehler wurden weitere Werte verarbeitet: {processed_values}"
    finally:
        # Cleanup
        disposable.dispose()
        await asyncio.sleep(0.2)  # Warte auf Cleanup


if __name__ == "__main__":

    async def run_tests():
        print("Testing endless operation...")
        await test_asubscribe_endless_operation()
        print("Endless operation test completed!")

        print("\nTesting self-completing operation...")
        await test_asubscribe_self_completing_operation()
        print("Self-completing operation test completed!")

        print("\nTesting error handling...")
        await test_asubscribe_error_handling()
        print("Error handling test completed!")

    asyncio.run(run_tests())
