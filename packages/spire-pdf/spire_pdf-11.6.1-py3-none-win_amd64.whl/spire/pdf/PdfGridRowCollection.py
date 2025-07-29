from enum import Enum
from plum import dispatch
from typing import TypeVar, Union, Generic, List, Tuple
from spire.pdf.common import *
from spire.pdf import *
from ctypes import *
import abc

class PdfGridRowCollection(SpireObject):
    """
    Represents a collection of rows in a PDF grid.
    """

    def Add(self) -> 'PdfGridRow':
        """
        Adds a new row to the collection.

        Returns:
            PdfGridRow: The newly added row.
        """
        GetDllLibPdf().PdfGridRowCollection_Add.argtypes = [c_void_p]
        GetDllLibPdf().PdfGridRowCollection_Add.restype = c_void_p
        intPtr = CallCFunction(GetDllLibPdf().PdfGridRowCollection_Add,self.Ptr)
        ret = None if intPtr == None else PdfGridRow(intPtr)
        return ret

    def SetSpan(self, rowIndex: int, cellIndex: int, rowSpan: int, colSpan: int):
        """
        Sets the span of a cell in the grid.

        Args:
            rowIndex (int): The index of the row.
            cellIndex (int): The index of the cell.
            rowSpan (int): The number of rows the cell should span.
            colSpan (int): The number of columns the cell should span.
        """
        GetDllLibPdf().PdfGridRowCollection_SetSpan.argtypes = [c_void_p, c_int, c_int, c_int, c_int]
        CallCFunction(GetDllLibPdf().PdfGridRowCollection_SetSpan,self.Ptr, rowIndex, cellIndex, rowSpan, colSpan)

    def ApplyStyle(self, style: 'PdfGridStyleBase'):
        """
        Applies a style to the grid.

        Args:
            style (PdfGridStyleBase): The style to apply.
        """
        intPtrstyle: c_void_p = style.Ptr

        GetDllLibPdf().PdfGridRowCollection_ApplyStyle.argtypes = [c_void_p, c_void_p]
        CallCFunction(GetDllLibPdf().PdfGridRowCollection_ApplyStyle,self.Ptr, intPtrstyle)