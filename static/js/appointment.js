document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("appointment_time");
    const preview = document.getElementById("previewText");
    const submitBtn = document.getElementById("submitBtn");
  
    if (!input) return;
  
    // Prevent past dates
    const now = new Date().toISOString().slice(0, 16);
    input.min = now;
  
    // Live preview
    input.addEventListener("change", () => {
  
      if (!input.value) {
        preview.textContent = "Not selected";
        submitBtn.disabled = true;
        return;
      }
  
      const date = new Date(input.value);
  
      const formatted = date.toLocaleString("en-IN", {
        dateStyle: "medium",
        timeStyle: "short"
      });
  
      preview.textContent = formatted;
      submitBtn.disabled = false;
  
    });
  
  });
  