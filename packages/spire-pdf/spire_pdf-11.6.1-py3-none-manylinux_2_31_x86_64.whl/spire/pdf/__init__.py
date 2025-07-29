import sys
from ctypes import *
from spire.pdf.common import *
from spire.pdf.common import dlllib
from spire.pdf.common import dlllibPdf

from spire.pdf.common.SpireObject import SpireObject

from spire.pdf.common.Common import IntPtrArray
from spire.pdf.common.Common import IntPtrWithTypeName
from spire.pdf.common.Common import GetObjVectorFromArray
from spire.pdf.common.Common import GetStrVectorFromArray
from spire.pdf.common.Common import GetVectorFromArray
from spire.pdf.common.Common import GetIntPtrArray
from spire.pdf.common.Common import GetByteArray
from spire.pdf.common.Common import GetIntValue
from spire.pdf.common.Common import GetObjIntPtr

from spire.pdf.common.RegexOptions import RegexOptions
from spire.pdf.common.CultureInfo import CultureInfo
from spire.pdf.common.Boolean import Boolean
from spire.pdf.common.Byte import Byte
from spire.pdf.common.Char import Char
from spire.pdf.common.Int16 import Int16
from spire.pdf.common.Int32 import Int32
from spire.pdf.common.Int64 import Int64
from spire.pdf.common.PixelFormat import PixelFormat
from spire.pdf.common.Size import Size
from spire.pdf.common.SizeF import SizeF
from spire.pdf.common.Point import Point
from spire.pdf.common.PointF import PointF
from spire.pdf.common.Rectangle import Rectangle
from spire.pdf.common.RectangleF import RectangleF
from spire.pdf.common.Single import Single
from spire.pdf.common.TimeSpan import TimeSpan
from spire.pdf.common.UInt16 import UInt16
from spire.pdf.common.UInt32 import UInt32
from spire.pdf.common.UInt64 import UInt64
from spire.pdf.common.Stream import Stream
from spire.pdf.common.License import License
from spire.pdf.common.Color import Color
from spire.pdf.common.DateTime import DateTime
from spire.pdf.common.Double import Double
from spire.pdf.common.EmfType import EmfType
from spire.pdf.common.Encoding import Encoding
from spire.pdf.common.FontStyle import FontStyle
from spire.pdf.common.GraphicsUnit import GraphicsUnit
from spire.pdf.common.ICollection import ICollection
from spire.pdf.common.IDictionary import IDictionary
from spire.pdf.common.IEnumerable import IEnumerable
from spire.pdf.common.IEnumerator import IEnumerator
from spire.pdf.common.IList import IList
from spire.pdf.common.String import String
from spire.pdf.common.Regex import Regex

from spire.pdf.Find_TextFindParameter import Find_TextFindParameter 
from spire.pdf.AspectRatio import AspectRatio 
from spire.pdf.CompressionLevel import CompressionLevel 
from spire.pdf.ConfiguerGraphicType import ConfiguerGraphicType 
from spire.pdf.CustomFieldType import CustomFieldType 
from spire.pdf.Clip import Clip 
from spire.pdf.DataFormat import DataFormat 
from spire.pdf.FileFormat import FileFormat 
from spire.pdf.FileRelatedFieldType import FileRelatedFieldType 
from spire.pdf.Find_TextFindParameter import Find_TextFindParameter 
from spire.pdf.GraphicMode import GraphicMode 
from spire.pdf.HttpMethod import HttpMethod 
from spire.pdf.HttpReadType import HttpReadType 
from spire.pdf.ImageFormatType import ImageFormatType 
from spire.pdf.ImageType import ImageType 
from spire.pdf.LayerExportState import LayerExportState 
from spire.pdf.LayerPrintState import LayerPrintState 
from spire.pdf.LayerViewState import LayerViewState 
from spire.pdf.LineType import LineType 
from spire.pdf.LoadHtmlType import LoadHtmlType 
from spire.pdf.Pdf3DActivationMode import Pdf3DActivationMode 
from spire.pdf.Pdf3DActivationState import Pdf3DActivationState 
from spire.pdf.PDF3DAnimationType import PDF3DAnimationType 
from spire.pdf.Pdf3DDeactivationMode import Pdf3DDeactivationMode 
from spire.pdf.Pdf3DDeactivationState import Pdf3DDeactivationState 
from spire.pdf.Pdf3DLightingStyle import Pdf3DLightingStyle 
from spire.pdf.Pdf3DProjectionClipStyle import Pdf3DProjectionClipStyle 
from spire.pdf.Pdf3DProjectionOrthoScaleMode import Pdf3DProjectionOrthoScaleMode 
from spire.pdf.Pdf3DProjectionType import Pdf3DProjectionType 
from spire.pdf.Pdf3DRenderStyle import Pdf3DRenderStyle 
from spire.pdf.PdfActionDestination import PdfActionDestination 
from spire.pdf.PdfAlignmentStyle import PdfAlignmentStyle 
from spire.pdf.PdfAnnotationFlags import PdfAnnotationFlags 
from spire.pdf.PdfAnnotationIntent import PdfAnnotationIntent 
from spire.pdf.PdfAnnotationWidgetTypes import PdfAnnotationWidgetTypes 
from spire.pdf.PdfAttachmentIcon import PdfAttachmentIcon 
from spire.pdf.PdfAttachmentRelationship import PdfAttachmentRelationship 
from spire.pdf.PdfBarcodeTextAlignment import PdfBarcodeTextAlignment 
from spire.pdf.PdfBlendMode import PdfBlendMode 
from spire.pdf.PdfBookletBindingMode import PdfBookletBindingMode 
from spire.pdf.PdfBorderEffect import PdfBorderEffect 
from spire.pdf.PdfBorderOverlapStyle import PdfBorderOverlapStyle 
from spire.pdf.PdfBorderStyle import PdfBorderStyle 
from spire.pdf.PdfButtonIconScaleMode import PdfButtonIconScaleMode 
from spire.pdf.PdfButtonIconScaleReason import PdfButtonIconScaleReason 
from spire.pdf.PdfButtonLayoutMode import PdfButtonLayoutMode 
from spire.pdf.PdfCertificationFlags import PdfCertificationFlags 
from spire.pdf.PdfCheckBoxStyle import PdfCheckBoxStyle 
from spire.pdf.PdfCjkFontFamily import PdfCjkFontFamily 
from spire.pdf.PdfColorSpace import PdfColorSpace 
from spire.pdf.PdfCompressionLevel import PdfCompressionLevel 
from spire.pdf.PdfConformanceLevel import PdfConformanceLevel 
from spire.pdf.PdfCrossReferenceType import PdfCrossReferenceType 
from spire.pdf.PdfDashStyle import PdfDashStyle 
from spire.pdf.PdfDestinationMode import PdfDestinationMode 
from spire.pdf.PdfDockStyle import PdfDockStyle 
from spire.pdf.PdfEncryptionAlgorithm import PdfEncryptionAlgorithm 
from spire.pdf.PdfEncryptionKeySize import PdfEncryptionKeySize 
from spire.pdf.PdfExtend import PdfExtend 
from spire.pdf.PdfFilePathType import PdfFilePathType 
from spire.pdf.PdfFillMode import PdfFillMode 
from spire.pdf.PdfFontFamily import PdfFontFamily 
from spire.pdf.PdfFontStyle import PdfFontStyle 
from spire.pdf.PdfFontType import PdfFontType 
from spire.pdf.PdfGraphicsUnit import PdfGraphicsUnit 
from spire.pdf.PdfHeaderSource import PdfHeaderSource 
from spire.pdf.PdfHighlightMode import PdfHighlightMode 
from spire.pdf.PdfHorizontalAlignment import PdfHorizontalAlignment 
from spire.pdf.PdfHorizontalOverflowType import PdfHorizontalOverflowType 
from spire.pdf.PdfImageType import PdfImageType 
from spire.pdf.PdfLayoutBreakType import PdfLayoutBreakType 
from spire.pdf.PdfLayoutType import PdfLayoutType 
from spire.pdf.PdfLinearGradientMode import PdfLinearGradientMode 
from spire.pdf.PdfLineBorderStyle import PdfLineBorderStyle 
from spire.pdf.PdfLineCap import PdfLineCap 
from spire.pdf.PdfLineCaptionType import PdfLineCaptionType 
from spire.pdf.PdfLineEndingStyle import PdfLineEndingStyle 
from spire.pdf.PdfLineIntent import PdfLineIntent 
from spire.pdf.PdfLineJoin import PdfLineJoin 
from spire.pdf.PdfListMarkerAlignment import PdfListMarkerAlignment 
from spire.pdf.PdfMatrixOrder import PdfMatrixOrder 
from spire.pdf.PdfNumberStyle import PdfNumberStyle 
from spire.pdf.PdfPageLayout import PdfPageLayout 
from spire.pdf.PdfPageMode import PdfPageMode 
from spire.pdf.PdfPageOrientation import PdfPageOrientation 
from spire.pdf.PdfPageRotateAngle import PdfPageRotateAngle 
from spire.pdf.PdfPermissionsFlags import PdfPermissionsFlags 
from spire.pdf.PdfPopupIcon import PdfPopupIcon 
from spire.pdf.PdfRubberStampAnnotationIcon import PdfRubberStampAnnotationIcon 
from spire.pdf.PdfSinglePageScalingMode import PdfSinglePageScalingMode 
from spire.pdf.PdfSoundChannels import PdfSoundChannels 
from spire.pdf.PdfSoundEncoding import PdfSoundEncoding 
from spire.pdf.PdfSoundIcon import PdfSoundIcon 
from spire.pdf.PdfSubmitFormFlags import PdfSubmitFormFlags 
from spire.pdf.PdfSubSuperScript import PdfSubSuperScript 
from spire.pdf.PdfTableDataSourceType import PdfTableDataSourceType 
from spire.pdf.PdfTextAlignment import PdfTextAlignment 
from spire.pdf.PdfTextAnnotationIcon import PdfTextAnnotationIcon 
from spire.pdf.PdfTextMarkupAnnotationType import PdfTextMarkupAnnotationType 
from spire.pdf.PdfTextStyle import PdfTextStyle 
from spire.pdf.PdfTransitionDimension import PdfTransitionDimension 
from spire.pdf.PdfTransitionDirection import PdfTransitionDirection 
from spire.pdf.PdfTransitionMotion import PdfTransitionMotion 
from spire.pdf.PdfTransitionStyle import PdfTransitionStyle 
from spire.pdf.PdfUnorderedMarkerStyle import PdfUnorderedMarkerStyle 
from spire.pdf.PdfVersion import PdfVersion 
from spire.pdf.PdfVerticalAlignment import PdfVerticalAlignment 
from spire.pdf.PdfVisibility import PdfVisibility 
from spire.pdf.PdfWordWrapType import PdfWordWrapType 
from spire.pdf.PrintScalingMode import PrintScalingMode 
from spire.pdf.Security_GraphicMode import Security_GraphicMode 
from spire.pdf.Security_SignImageLayout import Security_SignImageLayout 
from spire.pdf.SignatureConfiguerText import SignatureConfiguerText 
from spire.pdf.SignImageLayout import SignImageLayout 
from spire.pdf.SignInfoType import SignInfoType 
from spire.pdf.SignTextAlignment import SignTextAlignment 
from spire.pdf.StoreType import StoreType 
from spire.pdf.SubmitDataFormat import SubmitDataFormat 
from spire.pdf.TableWidthType import TableWidthType 
from spire.pdf.TabOrder import TabOrder 
from spire.pdf.TextAlign import TextAlign 
from spire.pdf.TextFindParameter import TextFindParameter 
from spire.pdf.TextLocation import TextLocation 
from spire.pdf.PdfPageLabels import PdfPageLabels 
from spire.pdf.PdfApplicationData import PdfApplicationData 
from spire.pdf.PdfPieceInfo import PdfPieceInfo 
from spire.pdf.PdfConvertOptions import PdfConvertOptions 
from spire.pdf.ReplaceActionType import ReplaceActionType 

from spire.pdf.PdfFileInfo import PdfFileInfo 

from spire.pdf.PdfPageTransition import PdfPageTransition 
from spire.pdf.PdfCollection import PdfCollection 
 
from spire.pdf.PdfDocumentPrivilege import PdfDocumentPrivilege 
from spire.pdf.PdfSecurityPolicy import PdfSecurityPolicy 
from spire.pdf.PdfPasswordSecurityPolicy import PdfPasswordSecurityPolicy 

from spire.pdf.PdfDocumentInformation import PdfDocumentInformation 
from spire.pdf.PdfViewerPreferences import PdfViewerPreferences 
from spire.pdf.PdfPageSize import PdfPageSize 

from spire.pdf.ImageQuality import ImageQuality 

from spire.pdf.PdfDocumentPageCollection import PdfDocumentPageCollection 
from spire.pdf.PdfMargins import PdfMargins 

from spire.pdf.PdfPageSettings import PdfPageSettings 

from spire.pdf.PdfBorders import PdfBorders 
from spire.pdf.PdfEdges import PdfEdges 
from spire.pdf.PdfPaddings import PdfPaddings 
 
from spire.pdf.PdfColumnCollection import PdfColumnCollection 
from spire.pdf.PdfColumn import PdfColumn 
from spire.pdf.PdfRow import PdfRow 
from spire.pdf.PdfRowCollection import PdfRowCollection 


from spire.pdf.PdfMarkerBase import PdfMarkerBase 
from spire.pdf.PdfOrderedMarker import PdfOrderedMarker 
from spire.pdf.PdfMarker import PdfMarker 
from spire.pdf.PdfListItem import PdfListItem 
from spire.pdf.PdfStringFormat import PdfStringFormat 
from spire.pdf.PdfFontBase import PdfFontBase 
from spire.pdf.PdfListItemCollection import PdfListItemCollection 


from spire.pdf.PdfHtmlLayoutFormat import PdfHtmlLayoutFormat 
from spire.pdf.PdfBlendBase import PdfBlendBase 
from spire.pdf.PdfBlend import PdfBlend 

from spire.pdf.PdfBrush import PdfBrush 
from spire.pdf.PdfBrushes import PdfBrushes 
from spire.pdf.PdfColorBlend import PdfColorBlend 
from spire.pdf.PdfTextLayout import PdfTextLayout 

from spire.pdf.PdfGridLayoutFormat import PdfGridLayoutFormat 

from spire.pdf.PdfGridCell import PdfGridCell 
from spire.pdf.PdfGridCellCollection import PdfGridCellCollection 
from spire.pdf.PdfGridColumn import PdfGridColumn 
from spire.pdf.PdfGridColumnCollection import PdfGridColumnCollection 
from spire.pdf.PdfGridRow import PdfGridRow 
from spire.pdf.PdfGridRowCollection import PdfGridRowCollection 
from spire.pdf.PdfGridHeaderCollection import PdfGridHeaderCollection 
from spire.pdf.PdfGridStyleBase import PdfGridStyleBase 
from spire.pdf.PdfGridStyle import PdfGridStyle 
from spire.pdf.PdfGridRowStyle import PdfGridRowStyle 
from spire.pdf.PdfGridCellStyle import PdfGridCellStyle 
from spire.pdf.PdfGridCellContent import PdfGridCellContent 
from spire.pdf.PdfGridCellContentList import PdfGridCellContentList 

from spire.pdf.PdfTableLayoutFormat import PdfTableLayoutFormat 


from spire.pdf.PdfRGBColor import PdfRGBColor 
from spire.pdf.PdfColorSpaces import PdfColorSpaces 
from spire.pdf.PdfComplexColor import PdfComplexColor
from spire.pdf.PdfCalGrayColor import PdfCalGrayColor 
from spire.pdf.PdfCalGrayColorSpace import PdfCalGrayColorSpace 
from spire.pdf.PdfCalRGBColor import PdfCalRGBColor 
from spire.pdf.PdfCalRGBColorSpace import PdfCalRGBColorSpace 

from spire.pdf.PdfDeviceColorSpace import PdfDeviceColorSpace 
from spire.pdf.PdfICCColor import PdfICCColor 
from spire.pdf.PdfICCColorSpace import PdfICCColorSpace 
from spire.pdf.PdfKnownColor import PdfKnownColor 
from spire.pdf.PdfKnownColorSpace import PdfKnownColorSpace 
from spire.pdf.PdfLabColor import PdfLabColor 
from spire.pdf.PdfLabColorSpace import PdfLabColorSpace 
from spire.pdf.PdfSeparationColor import PdfSeparationColor 
from spire.pdf.PdfSeparationColorSpace import PdfSeparationColorSpace 

from spire.pdf.PdfGraphicsState import PdfGraphicsState 

from spire.pdf.PdfUnitConvertor import PdfUnitConvertor 

from spire.pdf.PdfGradientBrush import PdfGradientBrush 
from spire.pdf.PdfLinearGradientBrush import PdfLinearGradientBrush 
from spire.pdf.PdfRadialGradientBrush import PdfRadialGradientBrush 
from spire.pdf.PdfSolidBrush import PdfSolidBrush 

from spire.pdf.PdfPen import PdfPen
from spire.pdf.PdfPens import PdfPens 

from spire.pdf.PdfCellStyle import PdfCellStyle 
from spire.pdf.PdfTableStyle import PdfTableStyle

#from spire.pdf.PdfTextFind import PdfTextFind 

from spire.pdf.PdfTextState import PdfTextState
from spire.pdf.PdfTextFragment import PdfTextFragment 
from spire.pdf.PdfTextFindOptions import PdfTextFindOptions 


from spire.pdf.PdfTextExtractOptions import PdfTextExtractOptions
#from spire.pdf.PdfTextFindCollection import PdfTextFindCollection

from spire.pdf.SimpleTextExtractionStrategy import SimpleTextExtractionStrategy 

from spire.pdf.PdfCanvas import PdfCanvas

from spire.pdf.PdfPageTemplateElement import PdfPageTemplateElement 

from spire.pdf.PdfStampCollection import PdfStampCollection
from spire.pdf.PdfDocumentTemplate import PdfDocumentTemplate 
from spire.pdf.PdfSectionTemplate import PdfSectionTemplate 

from spire.pdf.PdfTilingBrush import PdfTilingBrush 

from spire.pdf.PdfLayoutResult import PdfLayoutResult

from spire.pdf.PdfGraphicsWidget import PdfGraphicsWidget
from spire.pdf.PdfLayoutWidget import PdfLayoutWidget
from spire.pdf.PdfShapeWidget import PdfShapeWidget

from spire.pdf.PdfTemplate import PdfTemplate 

from spire.pdf.PdfImage import PdfImage

from spire.pdf.PdfPageBase import PdfPageBase
from spire.pdf.PdfTextReplaceOptions import PdfTextReplaceOptions 
from spire.pdf.PdfTextReplacer import PdfTextReplacer 
from spire.pdf.PdfTextExtractor import PdfTextExtractor
from spire.pdf.PdfTextFinder import PdfTextFinder 
from spire.pdf.PdfTableLayoutResult import PdfTableLayoutResult 
from spire.pdf.PdfLayoutHTMLResult import PdfLayoutHTMLResult 
from spire.pdf.PdfGridLayoutResult import PdfGridLayoutResult 

from spire.pdf.PdfGrid import PdfGrid 
from spire.pdf.PdfListBase import PdfListBase
from spire.pdf.PdfSortedList import PdfSortedList 
from spire.pdf.PdfList import PdfList 
from spire.pdf.PdfTable import PdfTable 
from spire.pdf.PdfMetafileLayoutFormat import PdfMetafileLayoutFormat 
 
from spire.pdf.PdfDrawWidget import PdfDrawWidget 
from spire.pdf.PdfFillElement import PdfFillElement
from spire.pdf.PdfPath import PdfPath 

from spire.pdf.PdfMask import PdfMask 
from spire.pdf.PdfColorMask import PdfColorMask

from spire.pdf.PdfBitmap import PdfBitmap
from spire.pdf.PdfTextLayoutResult import PdfTextLayoutResult 
from spire.pdf.PdfHTMLTextElement import PdfHTMLTextElement 
from spire.pdf.PdfTextWidget import PdfTextWidget 

from spire.pdf.PdfCjkStandardFont import PdfCjkStandardFont 
from spire.pdf.PdfTrueTypeFont import PdfTrueTypeFont 
from spire.pdf.LineInfo import LineInfo 
from spire.pdf.PdfStringLayoutResult import PdfStringLayoutResult 
from spire.pdf.PdfStringLayouter import PdfStringLayouter 
from spire.pdf.PdfMatrix import PdfMatrix 

from spire.pdf.PdfImageMask import PdfImageMask 
from spire.pdf.PdfMetafile import PdfMetafile 
from spire.pdf.PdfLayer import PdfLayer 
from spire.pdf.PdfLayerCollection import PdfLayerCollection 
from spire.pdf.PdfLayerOutline import PdfLayerOutline 
from spire.pdf.PdfUsedFont import PdfUsedFont 
from spire.pdf.XFAForm import XFAForm 
from spire.pdf.XfaField import XfaField 
from spire.pdf.XfaTextField import XfaTextField 
from spire.pdf.XfaCheckButtonField import XfaCheckButtonField 
from spire.pdf.XfaDateTimeField import XfaDateTimeField 
from spire.pdf.XfaChoiceListField import XfaChoiceListField 
from spire.pdf.XfaSignatureField import XfaSignatureField 
from spire.pdf.XfaButtonField import XfaButtonField 
from spire.pdf.XfaImageField import XfaImageField 
from spire.pdf.XfaBarcodeField import XfaBarcodeField 
from spire.pdf.XfaIntField import XfaIntField 
from spire.pdf.XfaFloatField import XfaFloatField 
from spire.pdf.XfaDoubleField import XfaDoubleField 
from spire.pdf.PdfPageCollection import PdfPageCollection 
from spire.pdf.PdfPageWidgetEnumerator import PdfPageWidgetEnumerator 
from spire.pdf.PdfAnnotation import PdfAnnotation 
 
from spire.pdf.IPdfTextBoxField import IPdfTextBoxField 

from spire.pdf.PdfField import PdfField 

from spire.pdf.PdfFieldWidget import PdfFieldWidget 

from spire.pdf.PdfAction import PdfAction
from spire.pdf.PdfJavaScriptAction import PdfJavaScriptAction
from spire.pdf.PdfFieldActions import PdfFieldActions

from spire.pdf.PdfStyledFieldWidget import PdfStyledFieldWidget 

from spire.pdf.PdfFieldWidgetItem import PdfFieldWidgetItem 

from spire.pdf.PdfStateWidgetItemCollection import PdfStateWidgetItemCollection

from spire.pdf.PdfButtonWidgetWidgetItem import PdfButtonWidgetWidgetItem 
from spire.pdf.PdfButtonWidgetItemCollection import PdfButtonWidgetItemCollection 
from spire.pdf.PdfButtonIconLayout import PdfButtonIconLayout 
from spire.pdf.PdfButtonWidgetFieldWidget import PdfButtonWidgetFieldWidget

from spire.pdf.PdfStateFieldWidget import PdfStateFieldWidget 
from spire.pdf.PdfStateWidgetItem import PdfStateWidgetItem 
from spire.pdf.PdfCheckBoxWidgetFieldWidget import PdfCheckBoxWidgetFieldWidget 
from spire.pdf.PdfCheckBoxWidgetWidgetItemCollection import PdfCheckBoxWidgetWidgetItemCollection 
from spire.pdf.PdfCheckBoxWidgetWidgetItem import PdfCheckBoxWidgetWidgetItem 
from spire.pdf.PdfComboBoxWidgetWidgetItem import PdfComboBoxWidgetWidgetItem 
from spire.pdf.PdfComboBoxWidgetItemCollection import PdfComboBoxWidgetItemCollection 
from spire.pdf.PdfStateItemCollection import PdfStateItemCollection 

from spire.pdf.PdfForm import PdfForm 

from spire.pdf.PdfFieldCollection import PdfFieldCollection

from spire.pdf.PdfAnnotationWidget import PdfAnnotationWidget

from spire.pdf.PdfStyledAnnotationWidget import PdfStyledAnnotationWidget

from spire.pdf.PdfMarkUpAnnotationWidget import PdfMarkUpAnnotationWidget

from spire.pdf.PdfRadioButtonListFieldWidget import PdfRadioButtonListFieldWidget 
from spire.pdf.PdfTextBoxFieldWidget import PdfTextBoxFieldWidget 
from spire.pdf.PdfRubberStampAnnotationWidget import PdfRubberStampAnnotationWidget


from spire.pdf.PdfListFieldWidgetItem import PdfListFieldWidgetItem 
from spire.pdf.PdfListWidgetFieldItemCollection import PdfListWidgetFieldItemCollection 
from spire.pdf.PdfListWidgetItem import PdfListWidgetItem 
from spire.pdf.PdfListWidgetItemCollection import PdfListWidgetItemCollection 
from spire.pdf.PdfRadioButtonWidgetItem import PdfRadioButtonWidgetItem
from spire.pdf.PdfRadioButtonWidgetWidgetItemCollection import PdfRadioButtonWidgetWidgetItemCollection 
from spire.pdf.PdfChoiceWidgetFieldWidget import PdfChoiceWidgetFieldWidget 
from spire.pdf.PdfListBoxWidgetFieldWidget import PdfListBoxWidgetFieldWidget
from spire.pdf.PdfComboBoxWidgetFieldWidget import PdfComboBoxWidgetFieldWidget

from spire.pdf.PdfSignatureFieldWidget import PdfSignatureFieldWidget
from spire.pdf.PdfFormFieldWidgetCollection import PdfFormFieldWidgetCollection 
from spire.pdf.PdfFormWidget import PdfFormWidget 



from spire.pdf.PdfFormFieldCollection import PdfFormFieldCollection 

from spire.pdf.PdfFieldWidgetImportError import PdfFieldWidgetImportError 
 
from spire.pdf.PdfTexBoxWidgetItem import PdfTexBoxWidgetItem 
from spire.pdf.PdfTextBoxWidgetItemCollection import PdfTextBoxWidgetItemCollection 
from spire.pdf.IPdfComboBoxField import IPdfComboBoxField 
from spire.pdf.PdfSignatureStyledField import PdfSignatureStyledField 



from spire.pdf.PdfStyledField import PdfStyledField
from spire.pdf.PdfCheckFieldBase import PdfCheckFieldBase 

from spire.pdf.PdfAppearanceField import PdfAppearanceField 
from spire.pdf.PdfButtonField import PdfButtonField 

from spire.pdf.PdfCheckBoxField import PdfCheckBoxField 
 
from spire.pdf.PdfListFieldItem import PdfListFieldItem 
from spire.pdf.PdfListFieldItemCollection import PdfListFieldItemCollection
from spire.pdf.PdfListField import PdfListField
from spire.pdf.PdfComboBoxField import PdfComboBoxField

from spire.pdf.PdfListBoxField import PdfListBoxField

from spire.pdf.PdfRadioButtonItemCollection import PdfRadioButtonItemCollection 
from spire.pdf.PdfRadioButtonListField import PdfRadioButtonListField 
from spire.pdf.PdfRadioButtonListItem import PdfRadioButtonListItem 

from spire.pdf.PdfSignatureAppearanceField import PdfSignatureAppearanceField 
from spire.pdf.PdfSignatureField import PdfSignatureField 
 
from spire.pdf.PdfTextBoxField import PdfTextBoxField 
from spire.pdf.PdfDestination import PdfDestination 

#class PdfBookmarkCollection (  IEnumerable) :
#    pass
from spire.pdf.PdfBookmark import PdfBookmark
from spire.pdf.PdfBookmarkCollection import PdfBookmarkCollection 
 
from spire.pdf.PdfBookmarkWidget import PdfBookmarkWidget
from spire.pdf.PdfFolder import PdfFolder 
 
from spire.pdf.PdfAutomaticField import PdfAutomaticField
 
from spire.pdf.PdfDynamicField import PdfDynamicField 
 
from spire.pdf.PdfMultipleValueField import PdfMultipleValueField
from spire.pdf.PdfCompositeField import PdfCompositeField
from spire.pdf.PdfMultipleNumberValueField import PdfMultipleNumberValueField 
 
from spire.pdf.PdfPageNumberField import PdfPageNumberField 
from spire.pdf.PdfSectionNumberField import PdfSectionNumberField 
from spire.pdf.PdfSectionPageCountField import PdfSectionPageCountField 
from spire.pdf.PdfSectionPageNumberField import PdfSectionPageNumberField 
from spire.pdf.PdfSingleValueField import PdfSingleValueField 
from spire.pdf.PdfPageCountField import PdfPageCountField
from spire.pdf.PdfDocumentAuthorField import PdfDocumentAuthorField
from spire.pdf.PdfStaticField import PdfStaticField 
 
from spire.pdf.PdfCreationDateField import PdfCreationDateField 
from spire.pdf.PdfDateTimeField import PdfDateTimeField 
from spire.pdf.PdfDestinationPageNumberField import PdfDestinationPageNumberField

from spire.pdf.PdfFileSpecificationBase import PdfFileSpecificationBase
from spire.pdf.PdfEmbeddedFileSpecification import PdfEmbeddedFileSpecification

from spire.pdf.PdfBarcodeQuietZones import PdfBarcodeQuietZones 
from spire.pdf.PdfBarcode import PdfBarcode 
from spire.pdf.PdfBarcodeException import PdfBarcodeException 

from spire.pdf.PdfUnidimensionalBarcode import PdfUnidimensionalBarcode
from spire.pdf.PdfCodabarBarcode import PdfCodabarBarcode 
from spire.pdf.PdfCode11Barcode import PdfCode11Barcode 
from spire.pdf.PdfCode128ABarcode import PdfCode128ABarcode 
from spire.pdf.PdfCode128BBarcode import PdfCode128BBarcode 
from spire.pdf.PdfCode128CBarcode import PdfCode128CBarcode 
from spire.pdf.PdfCode39Barcode import PdfCode39Barcode 
from spire.pdf.PdfCode32Barcode import PdfCode32Barcode 

from spire.pdf.PdfCode39ExtendedBarcode import PdfCode39ExtendedBarcode 
from spire.pdf.PdfCode93Barcode import PdfCode93Barcode 
from spire.pdf.PdfCode93ExtendedBarcode import PdfCode93ExtendedBarcode 
 
from spire.pdf.PdfList import PdfList 

from spire.pdf.PdfFont import PdfFont 
from spire.pdf.PdfToHtmlParameter import PdfToHtmlParameter 
from spire.pdf.Pdf3DActivation import Pdf3DActivation 
from spire.pdf.Pdf3DAnimation import Pdf3DAnimation 
from spire.pdf.Pdf3DBackground import Pdf3DBackground 
from spire.pdf.Pdf3DCrossSection import Pdf3DCrossSection 
from spire.pdf.Pdf3DCrossSectionCollection import Pdf3DCrossSectionCollection 
from spire.pdf.Pdf3DLighting import Pdf3DLighting 
from spire.pdf.Pdf3DNode import Pdf3DNode 
from spire.pdf.Pdf3DNodeCollection import Pdf3DNodeCollection 
from spire.pdf.Pdf3DProjection import Pdf3DProjection 
from spire.pdf.Pdf3DRendermode import Pdf3DRendermode 
from spire.pdf.Pdf3DView import Pdf3DView 
from spire.pdf.Pdf3DViewCollection import Pdf3DViewCollection 

from spire.pdf.LineBorder import LineBorder 

from spire.pdf.PdfLinkAnnotation import PdfLinkAnnotation 
from spire.pdf.PdfActionLinkAnnotation import PdfActionLinkAnnotation 
from spire.pdf.PdfActionAnnotation import PdfActionAnnotation
from spire.pdf.PdfFreeTextAnnotation import PdfFreeTextAnnotation 
from spire.pdf.PdfLineAnnotation import PdfLineAnnotation 
 


from spire.pdf.PdfFileAnnotation import PdfFileAnnotation
from spire.pdf.Pdf3DAnnotation import Pdf3DAnnotation 
from spire.pdf.PdfInkAnnotation import PdfInkAnnotation 
from spire.pdf.PdfInkAnnotationWidget import PdfInkAnnotationWidget 
from spire.pdf.PdfPolygonAnnotation import PdfPolygonAnnotation 
from spire.pdf.PdfPolyLineAnnotation import PdfPolyLineAnnotation 
from spire.pdf.PdfRubberStampAnnotation import PdfRubberStampAnnotation 
from spire.pdf.PdfWatermarkAnnotation import PdfWatermarkAnnotation 
from spire.pdf.PdfTextWebLink import PdfTextWebLink 
from spire.pdf.PdfTextMarkupAnnotation import PdfTextMarkupAnnotation 
 
from spire.pdf.PdfAttachmentAnnotationWidget import PdfAttachmentAnnotationWidget 
from spire.pdf.PdfCaretAnnotationWidget import PdfCaretAnnotationWidget 
from spire.pdf.PdfDocumentLinkAnnotationWidget import PdfDocumentLinkAnnotationWidget 
from spire.pdf.PdfFileLinkAnnotationWidget import PdfFileLinkAnnotationWidget 
from spire.pdf.PdfFreeTextAnnotationWidget import PdfFreeTextAnnotationWidget 
from spire.pdf.PdfLineAnnotationWidget import PdfLineAnnotationWidget 
 
from spire.pdf.PdfPolygonAndPolyLineAnnotationWidget import PdfPolygonAndPolyLineAnnotationWidget 
from spire.pdf.PdfPolygonAnnotationWidget import PdfPolygonAnnotationWidget 
from spire.pdf.PdfPolyLineAnnotationWidget import PdfPolyLineAnnotationWidget 
from spire.pdf.PdfPopupAnnotationWidget import PdfPopupAnnotationWidget 
from spire.pdf.PdfSoundAnnotationWidget import PdfSoundAnnotationWidget 
from spire.pdf.PdfSquareAnnotationWidget import PdfSquareAnnotationWidget 
 
from spire.pdf.PdfTextAnnotationWidget import PdfTextAnnotationWidget 
from spire.pdf.PdfTextMarkupAnnotationWidget import PdfTextMarkupAnnotationWidget 
from spire.pdf.PdfTextWebLinkAnnotationWidget import PdfTextWebLinkAnnotationWidget 
from spire.pdf.PdfUriAnnotationWidget import PdfUriAnnotationWidget 
from spire.pdf.PdfWatermarkAnnotationWidget import PdfWatermarkAnnotationWidget 
from spire.pdf.PdfWebLinkAnnotationWidget import PdfWebLinkAnnotationWidget 
from spire.pdf.PdfAnnotationBorder import PdfAnnotationBorder 
from spire.pdf.PdfAttachmentAnnotation import PdfAttachmentAnnotation 
from spire.pdf.PdfDocumentLinkAnnotation import PdfDocumentLinkAnnotation 
 
from spire.pdf.PdfFileLinkAnnotation import PdfFileLinkAnnotation 
from spire.pdf.PdfPopupAnnotation import PdfPopupAnnotation 
from spire.pdf.PdfSoundAnnotation import PdfSoundAnnotation 
from spire.pdf.PdfUriAnnotation import PdfUriAnnotation 
from spire.pdf.PdfAppearanceState import PdfAppearanceState 
from spire.pdf.PdfAppearance import PdfAppearance 
from spire.pdf.PdfExtendedAppearance import PdfExtendedAppearance 
 
from spire.pdf.PdfAnnotationCollection import PdfAnnotationCollection 
from spire.pdf.PdfAnnotationWidgetCollection import PdfAnnotationWidgetCollection

 
from spire.pdf.PdfActionCollection import PdfActionCollection
from spire.pdf.PdfFormAction import PdfFormAction 
from spire.pdf.PdfGoToAction import PdfGoToAction 
from spire.pdf.PdfGotoNameAction import PdfGotoNameAction 
 
from spire.pdf.PdfJavaScript import PdfJavaScript 
from spire.pdf.PdfLaunchAction import PdfLaunchAction 
from spire.pdf.PdfNamedAction import PdfNamedAction 
from spire.pdf.PdfAnnotationActions import PdfAnnotationActions 
from spire.pdf.PdfDocumentActions import PdfDocumentActions 
from spire.pdf.PdfEmbeddedGoToAction import PdfEmbeddedGoToAction 
 
from spire.pdf.PdfResetAction import PdfResetAction 

from spire.pdf.PdfSound import PdfSound 
from spire.pdf.PdfSoundAction import PdfSoundAction 
from spire.pdf.PdfSubmitAction import PdfSubmitAction 
from spire.pdf.PdfUriAction import PdfUriAction 
from spire.pdf.BookletOptions import BookletOptions 
from spire.pdf.MergerOptions import MergerOptions 
 
from spire.pdf.Utilities_PdfImageInfo import Utilities_PdfImageInfo 
from spire.pdf.PdfImageHelper import PdfImageHelper 
from spire.pdf.PdfMerger import PdfMerger 
from spire.pdf.Utilities_PdfTable import Utilities_PdfTable 
 
from spire.pdf.PdfTaggedContent import PdfTaggedContent 
from spire.pdf.PdfStructureTreeRoot import PdfStructureTreeRoot 
from spire.pdf.ArtifactPropertyList import ArtifactPropertyList 
from spire.pdf.PdfStandardStructTypes import PdfStandardStructTypes 
from spire.pdf.PdfAttributeOwner import PdfAttributeOwner 
from spire.pdf.PdfStructureAttributes import PdfStructureAttributes 
from spire.pdf.PdfStructContentItem import PdfStructContentItem 
from spire.pdf.IStructureNode import IStructureNode 
from spire.pdf.PdfStructureElement import PdfStructureElement 
from spire.pdf.PdfSignatureProperties import PdfSignatureProperties 
from spire.pdf.IPdfSignatureFormatter import IPdfSignatureFormatter 
from spire.pdf.Security_IPdfSignatureFormatter import Security_IPdfSignatureFormatter
from spire.pdf.PdfPKCS1Formatter import PdfPKCS1Formatter 
from spire.pdf.PdfPKCS7Formatter import PdfPKCS7Formatter 

from spire.pdf.ITSAService import ITSAService
from spire.pdf.TSAHttpService import TSAHttpService 
from spire.pdf.IOCSPService import IOCSPService
from spire.pdf.OCSPHttpService import OCSPHttpService 

from spire.pdf.IPdfSignatureAppearance import IPdfSignatureAppearance
from spire.pdf.PdfSignature import PdfSignature 
from spire.pdf.PdfSignatureMaker import PdfSignatureMaker
 
from spire.pdf.PdfSignatureAppearance import PdfSignatureAppearance 
from spire.pdf.PdfCustomAppearance import PdfCustomAppearance 



from spire.pdf.DocxOptions import DocxOptions 
from spire.pdf.OfdConverter import OfdConverter 
from spire.pdf.PdfToDocConverter import PdfToDocConverter 
from spire.pdf.PdfToWordConverter import PdfToWordConverter 
from spire.pdf.PdfToLinearizedPdfConverter import PdfToLinearizedPdfConverter 
from spire.pdf.PdfGrayConverter import PdfGrayConverter 
from spire.pdf.PdfStandardsConverter import PdfStandardsConverter 

from spire.pdf.XlsxOptions import XlsxOptions
from spire.pdf.XlsxLineLayoutOptions import XlsxLineLayoutOptions 
 
from spire.pdf.XlsxTextLayoutOptions import XlsxTextLayoutOptions 

from spire.pdf.OptimizationOptions import OptimizationOptions 
from spire.pdf.PdfCompressor import PdfCompressor 

from spire.pdf.PdfException import PdfException 
from spire.pdf.PdfDocumentException import PdfDocumentException 
from spire.pdf.PdfTableException import PdfTableException 
from spire.pdf.PdfConformanceException import PdfConformanceException 
from spire.pdf.PdfAnnotationException import PdfAnnotationException 
 
from spire.pdf.PdfCertificate import PdfCertificate 
from spire.pdf.PdfSecurity import PdfSecurity 

from spire.pdf.PdfPageWidget import PdfPageWidget 
from spire.pdf.PdfNewPage import PdfNewPage 
from spire.pdf.PdfSectionPageCollection import PdfSectionPageCollection 
from spire.pdf.PdfSection import PdfSection 
from spire.pdf.PdfSectionCollection import PdfSectionCollection 

from spire.pdf.PdfAttachment import PdfAttachment 
from spire.pdf.Collections_PdfCollection import Collections_PdfCollection 
from spire.pdf.PdfAttachmentCollection import PdfAttachmentCollection

from spire.pdf.PdfDocumentBase import PdfDocumentBase 
from spire.pdf.PdfDocument import PdfDocument 

from spire.pdf.PdfTableExtractor import PdfTableExtractor 
from spire.pdf.PdfBookletCreator import PdfBookletCreator

from spire.pdf.PdfNewDocument import PdfNewDocument

from spire.pdf.PdfCompareOptions import PdfCompareOptions 
from spire.pdf.PdfComparer import PdfComparer 
from spire.pdf.PdfOrdinarySignatureMaker import PdfOrdinarySignatureMaker 
from spire.pdf.PdfMDPSignatureMaker import PdfMDPSignatureMaker

from spire.pdf.Security_PdfSignature import Security_PdfSignature 
 