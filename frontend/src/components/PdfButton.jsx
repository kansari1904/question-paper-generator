
import { useState } from "react";
import { Download, Loader2 } from "lucide-react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import toast from "react-hot-toast";

function PdfButton() {
  const [generating, setGenerating] = useState(false);

  const generatePdf = async () => {
    const original = document.getElementById("paper");

    if (!original) {
      toast.error("Question paper not found.");
      return;
    }

    setGenerating(true);

    let printPaper = null;

    try {
      /*
       * ------------------------------------------------------------
       * 1. Create a dedicated PDF DOM
       * ------------------------------------------------------------
       */

      printPaper = original.cloneNode(true);

      printPaper.id = "pdf-paper";

      Object.assign(printPaper.style, {
        position: "absolute",
        left: "-100000px",
        top: "0",
        width: "210mm",
        minHeight: "297mm",
        background: "#ffffff",
        color: "#0f172a",
        padding: "15mm",
        margin: "0",
        boxSizing: "border-box",
        overflow: "visible",
        fontFamily:
          "Arial, Helvetica, sans-serif",
      });

      /*
       * Remove interactive controls.
       */
      printPaper
        .querySelectorAll("button")
        .forEach((button) => button.remove());

      /*
       * ------------------------------------------------------------
       * 2. PDF-safe styling
       * ------------------------------------------------------------
       */

      const style = document.createElement("style");

      style.textContent = `
#pdf - paper,
    #pdf - paper * {
        box- sizing: border - box!important;
        }

#pdf - paper {
    width: 210mm!important;
    min - height: 297mm!important;
    padding: 15mm!important;
    margin: 0!important;
    background: #ffffff!important;
    color: #0f172a!important;
    font - family: Arial, Helvetica, sans - serif!important;
}

#pdf - paper p,
    #pdf - paper h1,
        #pdf - paper h2,
            #pdf - paper h3,
                #pdf - paper span,
                    #pdf - paper div {
    color: #0f172a;
}

/*
 * Paper header
 */
#pdf - paper header {
    border - color: #0f172a!important;
    margin - bottom: 0!important;
}

/*
 * Section heading
 */
#pdf - paper section {
    margin - top: 7mm!important;
}

#pdf - paper section: first - of - type {
    margin - top: 7mm!important;
}

/*
 * Keep section title with its first question.
 */
#pdf - paper section > div: first - child {
    break-after: avoid!important;
    page -break-after: avoid!important;
}

/*
 * Question block.
 *
 * The complete question card must stay together:
 * question text + marks + options + metadata.
 */
#pdf - paper.question - card {
    break-inside: avoid!important;
    page -break-inside: avoid!important;

    margin: 0!important;
    padding - top: 5mm!important;
    padding - bottom: 5mm!important;

    border - bottom: 1px solid #cbd5e1!important;
}

/*
 * Don't split MCQ options.
 */
#pdf - paper.question - card > div {
    break-inside: avoid!important;
    page -break-inside: avoid!important;
}

/*
 * Options.
 */
#pdf - paper.question - card.grid {
    display: grid!important;
    grid - template - columns: 1fr 1fr!important;
    column - gap: 10mm!important;
    row - gap: 2mm!important;
}

/*
 * Remove web-only effects.
 */
#pdf - paper button {
    display: none!important;
}

/*
 * Avoid unnecessary large gaps.
 */
#pdf - paper.mt - 8 {
    margin - top: 7mm!important;
}

#pdf - paper.mt - 7 {
    margin - top: 5mm!important;
}

#pdf - paper.mt - 6 {
    margin - top: 4mm!important;
}

#pdf - paper.mt - 5 {
    margin - top: 3mm!important;
}

#pdf - paper.mt - 4 {
    margin - top: 3mm!important;
}

#pdf - paper.mt - 3 {
    margin - top: 2mm!important;
}

#pdf - paper.mt - 2 {
    margin - top: 1.5mm!important;
}

/*
 * Keep normal exam-paper line height.
 */
#pdf - paper p {
    line - height: 1.55!important;
}

/*
 * Avoid flex layouts causing unnecessary vertical space.
 */
#pdf - paper.flex - col {
    flex - direction: row!important;
}

/*
 * Header student information should remain in two columns.
 */
#pdf - paper header.grid {
    display: grid!important;
    grid - template - columns: 1fr 1fr!important;
    gap: 4mm 10mm!important;
}
`;

      printPaper.appendChild(style);
      document.body.appendChild(printPaper);

      /*
       * Give browser time to calculate layout.
       */
      await new Promise((resolve) => setTimeout(resolve, 300));

      /*
       * ------------------------------------------------------------
       * 3. Render the complete paper
       * ------------------------------------------------------------
       */

      const canvas = await html2canvas(printPaper, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
        logging: false,

        /*
         * Explicitly avoid transparent/unsupported colors.
         */
        onclone: (clonedDocument) => {
          const clonedPaper =
            clonedDocument.getElementById("pdf-paper");

          if (!clonedPaper) return;

          clonedPaper.style.backgroundColor = "#ffffff";
          clonedPaper.style.color = "#0f172a";

          clonedPaper
            .querySelectorAll("*")
            .forEach((element) => {
              element.style.backgroundImage = "none";

              /*
               * Replace any potentially problematic computed
               * background colors.
               */
              const computed =
                clonedDocument.defaultView.getComputedStyle(
                  element
                );

              if (
                computed.backgroundColor.includes("oklch")
              ) {
                element.style.backgroundColor = "#ffffff";
              }

              if (computed.color.includes("oklch")) {
                element.style.color = "#0f172a";
              }
            });
        },
      });

      /*
       * ------------------------------------------------------------
       * 4. A4 PDF configuration
       * ------------------------------------------------------------
       */

      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
        compress: true,
      });

      const pageWidth = 210;
      const pageHeight = 297;

      const margin = 15;

      const contentWidth = pageWidth - margin * 2;
      const contentHeight = pageHeight - margin * 2;

      /*
       * Canvas represents the complete 210mm-wide PDF paper.
       */
      const pxPerMm = canvas.width / pageWidth;

      const pageHeightPx =
        contentHeight * pxPerMm;

      /*
       * ------------------------------------------------------------
       * 5. Find question boundaries
       * ------------------------------------------------------------
       */

      const questionElements = [
        ...printPaper.querySelectorAll(
          ".question-card"
        ),
      ];

      const sectionElements = [
        ...printPaper.querySelectorAll(
          "section"
        ),
      ];

      /*
       * Convert DOM coordinates into canvas coordinates.
       */
      const paperRect =
        printPaper.getBoundingClientRect();

      const questions = questionElements.map(
        (element) => {
          const rect =
            element.getBoundingClientRect();

          return {
            element,
            top:
              (rect.top - paperRect.top) *
              (canvas.width /
                printPaper.offsetWidth),

            bottom:
              (rect.bottom - paperRect.top) *
              (canvas.width /
                printPaper.offsetWidth),
          };
        }
      );

      /*
       * ------------------------------------------------------------
       * 6. Build intelligent page cuts
       *
       * We fill the current page as much as possible.
       *
       * IMPORTANT:
       * A question is never split.
       * ------------------------------------------------------------
       */

      const pageRanges = [];

      let currentStart = 0;

      /*
       * The printable area starts after the top margin.
       */
      const topMarginPx = margin * pxPerMm;

      /*
       * The printable bottom boundary.
       */
      const bottomMarginPx =
        topMarginPx + pageHeightPx;

      let pageStartContent = 0;

      /*
       * We work through questions one by one.
       */
      for (let i = 0; i < questions.length; i++) {
        const question = questions[i];

        /*
         * Absolute position inside the complete canvas.
         */
        const questionTop = question.top;
        const questionBottom = question.bottom;

        /*
         * First question on the current page.
         */
        if (pageStartContent === 0) {
          pageStartContent = 0;
        }

        /*
         * Current page's printable bottom.
         */
        const currentPageBottom =
          pageStartContent +
          pageHeightPx;

        /*
         * If the question does not fit, start a new page
         * BEFORE this question.
         */
        if (
          questionBottom > currentPageBottom &&
          questionTop > pageStartContent
        ) {
          pageRanges.push({
            start: pageStartContent,
            end: questionTop,
          });

          pageStartContent = questionTop;
        }
      }

      /*
       * Add final page.
       */
      if (pageStartContent < canvas.height) {
        pageRanges.push({
          start: pageStartContent,
          end: canvas.height,
        });
      }

      /*
       * If no ranges were created, use complete canvas.
       */
      if (pageRanges.length === 0) {
        pageRanges.push({
          start: 0,
          end: canvas.height,
        });
      }

      /*
       * ------------------------------------------------------------
       * 7. Draw each page
       * ------------------------------------------------------------
       */

      for (
        let pageIndex = 0;
        pageIndex < pageRanges.length;
        pageIndex++
      ) {
        if (pageIndex > 0) {
          pdf.addPage();
        }

        const range = pageRanges[pageIndex];

        const sliceStart = Math.max(
          0,
          Math.floor(range.start)
        );

        const sliceEnd = Math.min(
          canvas.height,
          Math.ceil(range.end)
        );

        const sliceHeight =
          sliceEnd - sliceStart;

        /*
         * Create page-sized canvas.
         */
        const pageCanvas =
          document.createElement("canvas");

        pageCanvas.width = canvas.width;
        pageCanvas.height = sliceHeight;

        const pageContext =
          pageCanvas.getContext("2d");

        pageContext.fillStyle = "#ffffff";
        pageContext.fillRect(
          0,
          0,
          pageCanvas.width,
          pageCanvas.height
        );

        /*
         * Copy only this page's portion.
         */
        pageContext.drawImage(
          canvas,
          0,
          sliceStart,
          canvas.width,
          sliceHeight,
          0,
          0,
          canvas.width,
          sliceHeight
        );

        /*
         * Convert to image.
         */
        const imageData =
          pageCanvas.toDataURL(
            "image/jpeg",
            0.95
          );

        /*
         * Calculate rendered height.
         */
        const renderedHeight =
          sliceHeight / pxPerMm;

        /*
         * Never exceed printable area.
         */
        const finalHeight = Math.min(
          renderedHeight,
          contentHeight
        );

        /*
         * Center vertically only if there is a tiny
         * leftover area. This prevents huge blank spaces.
         */
        const verticalOffset =
          renderedHeight < contentHeight
            ? 0
            : 0;

        pdf.addImage(
          imageData,
          "JPEG",
          margin,
          margin + verticalOffset,
          contentWidth,
          finalHeight,
          undefined,
          "FAST"
        );
      }

      /*
       * ------------------------------------------------------------
       * 8. Save
       * ------------------------------------------------------------
       */

      pdf.save(
        "smartpaper-question-paper.pdf"
      );

      toast.success(
        "Question paper PDF downloaded successfully."
      );
    } catch (error) {
      console.error(
        "PDF generation error:",
        error
      );

      toast.error(
        "Failed to generate PDF."
      );
    } finally {
      /*
       * Always remove temporary DOM.
       */
      if (printPaper?.parentNode) {
        printPaper.parentNode.removeChild(
          printPaper
        );
      }

      setGenerating(false);
    }
  };

  return (
    <button
      type="button"
      onClick={generatePdf}
      disabled={generating}
      className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {generating ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Preparing PDF...
        </>
      ) : (
        <>
          <Download className="h-4 w-4" />
          Download PDF
        </>
      )}
    </button>
  );
}

export default PdfButton;
