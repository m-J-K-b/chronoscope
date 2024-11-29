const faviconURL = "/static/images/favicon.svg"; // Update the path if necessary

fetch(faviconURL)
  .then((response) => response.text())
  .then((svgContent) => {
    const parser = new DOMParser();
    const svgDoc = parser.parseFromString(svgContent, "image/svg+xml");
    const svgElement = svgDoc.documentElement; // Select the <svg> element itself

    // Function to update the favicon dynamically
    function updateFavicon(fillColor) {
      svgElement.setAttribute("fill", fillColor); // Apply fill color to the entire SVG
      const svgBlob = new Blob([svgElement.outerHTML], {
        type: "image/svg+xml",
      });
      const url = URL.createObjectURL(svgBlob);

      const favicon = document.querySelector("link[rel='icon']");
      if (favicon) {
        favicon.href = url;
      } else {
        const newFavicon = document.createElement("link");
        newFavicon.rel = "icon";
        newFavicon.href = url;
        document.head.appendChild(newFavicon);
      }
    }

    // Change favicon color based on focus/blur
    window.addEventListener("focus", () => updateFavicon("black"));
    window.addEventListener("blur", () => updateFavicon("white"));
  });
