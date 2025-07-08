// script.js
document.addEventListener("DOMContentLoaded", function () {
  // Add floating shapes to body
  const floatingShapes = document.createElement("div");
  floatingShapes.className = "floating-shapes";
  floatingShapes.innerHTML = `
      <div class="shape"></div>
      <div class="shape"></div>
      <div class="shape"></div>
      <div class="shape"></div>
  `;
  document.body.appendChild(floatingShapes);

  // Add form header
  const form = document.querySelector("form");
  const formHeader = document.createElement("div");
  formHeader.className = "form-header";
  formHeader.innerHTML = `
      <h1 class="form-title">Data Prediction Form</h1>
      <p class="form-subtitle">Please fill out the form below to get your prediction</p>
  `;
  form.insertBefore(formHeader, form.firstChild);

  // Add progress bar
  const progressBar = document.createElement("div");
  progressBar.className = "progress-bar";
  progressBar.innerHTML = '<div class="progress-fill" id="progressFill"></div>';
  form.insertBefore(progressBar, form.children[1]);

  // Wrap form elements in groups and enhance styling
  const labels = form.querySelectorAll("label");
  labels.forEach((label, index) => {
    // Skip if it's already processed or is a checkbox label
    if (label.closest(".form-group") || label.closest(".checkbox-item")) {
      return;
    }

    const formGroup = document.createElement("div");
    formGroup.className = "form-group";
    formGroup.style.animationDelay = `${index * 0.1}s`;

    // Get the next elements until we hit another label or the submit button
    let nextElement = label.nextElementSibling;
    const elementsToMove = [label];

    while (
      nextElement &&
      nextElement.tagName !== "LABEL" &&
      nextElement.type !== "submit"
    ) {
      elementsToMove.push(nextElement);
      nextElement = nextElement.nextElementSibling;
    }

    // Insert the form group before the first element
    label.parentNode.insertBefore(formGroup, label);

    // Move elements into the form group
    elementsToMove.forEach((element) => {
      formGroup.appendChild(element);
    });
  });

  // Enhanced checkbox styling with proper alignment
  console.log("Starting checkbox enhancement...");
  const processedCheckboxNames = new Set();

  // Find all main labels that have checkboxes
  const mainLabels = form.querySelectorAll("label[for]");
  console.log("Found main labels:", mainLabels.length);

  mainLabels.forEach((mainLabel) => {
    const checkboxName = mainLabel.getAttribute("for");
    const checkboxes = form.querySelectorAll(
      `input[type="checkbox"][name="${checkboxName}"]`
    );
    console.log(
      `Processing ${checkboxName}, found ${checkboxes.length} checkboxes`
    );

    if (checkboxes.length > 0 && !processedCheckboxNames.has(checkboxName)) {
      processedCheckboxNames.add(checkboxName);

      // Create container for checkboxes
      const container = document.createElement("div");
      container.className = "checkbox-container";

      // Process checkboxes and their labels
      checkboxes.forEach((checkbox, index) => {
        console.log(`Processing checkbox ${index} for ${checkboxName}`);

        // Find the associated label - specific to your HTML structure
        let associatedLabel = null;
   

        let currentElement = checkbox.nextSibling;
        while (currentElement) {
          // Skip text nodes (like whitespace) and br tags
          if (
            currentElement.nodeType === Node.TEXT_NODE ||
            (currentElement.nodeType === Node.ELEMENT_NODE &&
              currentElement.tagName === "BR")
          ) {
            currentElement = currentElement.nextSibling;
            continue;
          }

          // Found a label element without 'for' attribute - this is our target
          if (
            currentElement.nodeType === Node.ELEMENT_NODE &&
            currentElement.tagName === "LABEL" &&
            !currentElement.hasAttribute("for")
          ) {
            associatedLabel = currentElement;
            labelText = currentElement.textContent.trim();
            console.log(`Found label for checkbox ${index}: "${labelText}"`);
            break;
          }

          // Stop if we hit another checkbox or a main label (with 'for' attribute)
          if (
            currentElement.nodeType === Node.ELEMENT_NODE &&
            ((currentElement.tagName === "INPUT" &&
              currentElement.type === "checkbox") ||
              (currentElement.tagName === "LABEL" &&
                currentElement.hasAttribute("for")))
          ) {
            break;
          }

          currentElement = currentElement.nextSibling;
        }

        // Fallback: use the checkbox value if no label found
        if (!labelText && checkbox.value) {
          labelText = checkbox.value;
          console.log(
            `Using checkbox value as label for checkbox ${index}: "${labelText}"`
          );
        }

        // Create checkbox item with proper structure
        const item = document.createElement("div");
        item.className = "checkbox-item";

        // Create a label wrapper that contains both checkbox and text
        const labelWrapper = document.createElement("label");
        labelWrapper.className = "checkbox-label";
        labelWrapper.style.display = "flex";
        labelWrapper.style.alignItems = "center";
        labelWrapper.style.cursor = "pointer";
        labelWrapper.style.margin = "0";
        labelWrapper.style.fontWeight = "500";

        // Clone the checkbox
        const checkboxClone = checkbox.cloneNode(true);
        checkboxClone.style.marginRight = "0.75rem";
        checkboxClone.style.marginBottom = "0";

        // Get label text
        const labelText = associatedLabel
          ? associatedLabel.textContent.trim()
          : `Option ${index + 1}`;

        // Create text span
        const textSpan = document.createElement("span");
        textSpan.textContent = labelText;
        textSpan.style.lineHeight = "1.4";
        textSpan.style.color = "#333";

        // Append checkbox and text to label wrapper
        labelWrapper.appendChild(checkboxClone);
        labelWrapper.appendChild(textSpan);

        // Add label wrapper to item
        item.appendChild(labelWrapper);
        container.appendChild(item);

        // Hide original elements
        checkbox.style.display = "none";
        if (associatedLabel) {
          associatedLabel.style.display = "none";
        }

        console.log(`Created checkbox item ${index} with text: "${labelText}"`);
      });

      // Insert container after the main label
      let insertPoint = mainLabel.nextSibling;
      while (insertPoint && insertPoint.nodeType === Node.TEXT_NODE) {
        insertPoint = insertPoint.nextSibling;
      }

      if (insertPoint) {
        mainLabel.parentNode.insertBefore(container, insertPoint);
      } else {
        mainLabel.parentNode.appendChild(container);
      }

      console.log(
        `Created container for ${checkboxName} with ${checkboxes.length} items`
      );
    }
  });

  // Progress bar functionality
  const progressFill = document.getElementById("progressFill");
  const formInputs = form.querySelectorAll(
    'input[type="text"], select, input[type="checkbox"]'
  );

  function updateProgress() {
    let filledInputs = 0;
    const processedCheckboxGroups = new Set();

    formInputs.forEach((input) => {
      if (input.type === "checkbox") {
        const checkboxName = input.name;
        if (!processedCheckboxGroups.has(checkboxName)) {
          processedCheckboxGroups.add(checkboxName);
          const checkboxGroup = form.querySelectorAll(
            `input[type="checkbox"][name="${checkboxName}"]`
          );
          const hasCheckedBox = Array.from(checkboxGroup).some(
            (cb) => cb.checked
          );
          if (hasCheckedBox) {
            filledInputs++;
          }
        }
      } else if (input.value.trim() !== "") {
        filledInputs++;
      }
    });

    const totalInputs =
      form.querySelectorAll('input[type="text"], select').length +
      processedCheckboxGroups.size;
    const progress = (filledInputs / totalInputs) * 100;
    progressFill.style.width = progress + "%";
  }

  // Add event listeners for progress tracking
  formInputs.forEach((input) => {
    input.addEventListener("input", updateProgress);
    input.addEventListener("change", updateProgress);
  });

  // Form submission with loading state
  form.addEventListener("submit", function (e) {
    const submitBtn = form.querySelector('input[type="submit"]');
    submitBtn.value = "Processing...";
    submitBtn.disabled = true;
  });

  // Add placeholder text to inputs
  const textInputs = form.querySelectorAll('input[type="text"]');
  textInputs.forEach((input) => {
    const label = input.closest(".form-group").querySelector("label");
    if (label) {
      const labelText = label.textContent.replace("_", " ").toLowerCase();
      input.placeholder = `Enter ${labelText}`;
    }
  });

  // Add default option text to selects
  const selects = form.querySelectorAll("select");
  selects.forEach((select) => {
    const defaultOption = select.querySelector('option[value=""]');
    if (defaultOption) {
      defaultOption.textContent = "-- Select an option --";
    }
  });

  // Clean up extra <br> tags
  const brTags = form.querySelectorAll("br");
  brTags.forEach((br) => br.remove());

  // Initial progress update
  updateProgress();
});
