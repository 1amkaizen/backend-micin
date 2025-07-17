// static/js/progress.js
document.addEventListener("DOMContentLoaded", function () {
  console.log("🧠 progress.js loaded");

  const iframes = document.querySelectorAll("iframe[data-module-id]");
  console.log("🔍 Found", iframes.length, "iframes with data-module-id");

  iframes.forEach((iframe) => {
    const moduleId = iframe.getAttribute("data-module-id");
    const player = new Vimeo.Player(iframe);

    player.on("ended", function () {
      console.log("✅ Video ended, sending progress for module:", moduleId);

      fetch(`/progress/${moduleId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin", // penting agar cookie session ikut
      })
        .then(async (res) => {
          // static/js/progress.js
          document.addEventListener("DOMContentLoaded", function () {
            console.log("🧠 progress.js loaded");

            const iframes = document.querySelectorAll("iframe[data-module-id]");
            console.log(
              "🔍 Found",
              iframes.length,
              "iframes with data-module-id"
            );

            iframes.forEach((iframe) => {
              const moduleId = iframe.getAttribute("data-module-id");
              const player = new Vimeo.Player(iframe);

              player.on("ended", function () {
                console.log(
                  "✅ Video ended, sending progress for module:",
                  moduleId
                );

                fetch(`/progress/${moduleId}`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  credentials: "same-origin", // penting agar cookie session ikut
                })
                  .then(async (res) => {
                    if (res.ok) {
                      console.log("✅ Progress updated for module:", moduleId);
                    } else {
                      const errorText = await res.text();
                      console.error("❌ Failed to update progress:", errorText);
                    }
                  })
                  .catch((err) => {
                    console.error(
                      "❌ Network error while sending progress:",
                      err
                    );
                  });
              });
            });
          });

          if (res.ok) {
            console.log("✅ Progress updated for module:", moduleId);
          } else {
            const errorText = await res.text();
            console.error("❌ Failed to update progress:", errorText);
          }
        })
        .catch((err) => {
          console.error("❌ Network error while sending progress:", err);
        });
    });
  });
});
