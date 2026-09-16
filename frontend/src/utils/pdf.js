import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

export async function downloadPaperPDF(paper) {
  const element = document.getElementById('question-paper')

  if (!element) {
    console.error('Question paper element not found')
    return
  }

  try {
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
    })

    const imageData = canvas.toDataURL('image/png')

    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    })

    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()

    const margin = 10

    const availableWidth = pageWidth - margin * 2
    const imageHeight =
      (canvas.height * availableWidth) / canvas.width

    let heightLeft = imageHeight
    let position = margin

    pdf.addImage(
      imageData,
      'PNG',
      margin,
      position,
      availableWidth,
      imageHeight
    )

    heightLeft -= pageHeight - margin * 2

    while (heightLeft > 0) {
      position =
        heightLeft - imageHeight + margin

      pdf.addPage()

      pdf.addImage(
        imageData,
        'PNG',
        margin,
        position,
        availableWidth,
        imageHeight
      )

      heightLeft -= pageHeight - margin * 2
    }

    const fileName = createFileName(paper)

    pdf.save(fileName)
  } catch (error) {
    console.error('PDF generation failed:', error)
  }
}

function createFileName(paper) {
  const id = paper?.paper_id
    ? String(paper.paper_id).slice(0, 8)
    : 'paper'

  return `science-question-paper-${id}.pdf`
}