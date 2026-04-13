"""
Test per il vocabolario planning_mode (DL-ARCH-V2-027, TASK-V2-069).

Verifica la mappatura centrale resolve_planning_mode:
- True  -> "by_article"
- False -> "by_customer_order_line"
- None  -> None
"""

import pytest

from nssp_v2.core.planning_mode import resolve_planning_mode


class TestResolvePlanningMode:

    def test_true_restituisce_by_article(self):
        assert resolve_planning_mode(True) == "by_article"

    def test_false_restituisce_by_customer_order_line(self):
        assert resolve_planning_mode(False) == "by_customer_order_line"

    def test_none_restituisce_none(self):
        assert resolve_planning_mode(None) is None

    def test_mapping_esaustivo(self):
        """Verifica che tutti i valori ammessi siano coperti."""
        assert resolve_planning_mode(True) is not None
        assert resolve_planning_mode(False) is not None
        assert resolve_planning_mode(None) is None

    def test_valori_attesi_sono_stringhe_letterali(self):
        """Il tipo restituito e una stringa letterale, non un enum."""
        result_true = resolve_planning_mode(True)
        result_false = resolve_planning_mode(False)
        assert isinstance(result_true, str)
        assert isinstance(result_false, str)
        assert result_true == "by_article"
        assert result_false == "by_customer_order_line"
