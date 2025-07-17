function initSolanaForm() {
  const form = document.getElementById("solanaForm");
  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const full_name = form.full_name.value.trim();
    const wallet = form.wallet.value.trim();
    const nominal = form.nominal.value;

    if (!full_name || !wallet || !nominal) {
      alert("Isi semua data dengan benar!");
      return;
    }

    try {
      const res = await fetch("/bayar/solana", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name, wallet, nominal }),
      });

      const data = await res.json();

      if (data.error) {
        alert(data.error);
        return;
      }

      window.snap.pay(data.snap_token, {
        onSuccess: function (result) {
          alert("Pembayaran berhasil!");
        },
        onPending: function (result) {
          alert("Pembayaran pending.");
        },
        onError: function (result) {
          alert("Pembayaran gagal: " + result.status_message);
        },
        onClose: function () {
          alert("Popup pembayaran ditutup.");
        },
      });
    } catch (err) {
      alert("Terjadi kesalahan: " + err.message);
    }
  });
}
