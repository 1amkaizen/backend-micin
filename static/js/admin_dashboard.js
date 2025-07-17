function toggleExamForm() {
  document.getElementById("exam-form").style.display = "block";
  document.getElementById("exam-list").style.display = "none";
}

async function loadExamList() {
  document.getElementById("exam-form").style.display = "none";
  document.getElementById("exam-list").style.display = "block";

  const res = await fetch("/admin/exams");
  const exams = await res.json();

  const tbody = document.getElementById("exam-table-body");
  tbody.innerHTML = "";

  const optionLabels = ["A", "B", "C", "D"];

  exams.forEach((exam) => {
    const row = document.createElement("tr");

    const ops = exam.options
      .map((opt, i) => {
        const label = optionLabels[i] || `(${i})`;
        const isCorrect = i === exam.answer;
        return `<li${
          isCorrect ? ' style="font-weight:bold; color:green;"' : ""
        }>${label}. ${opt}</li>`;
      })
      .join("");

    row.innerHTML = `
      <td>${exam.level}</td>
      <td>${exam.question}</td>
      <td><ul>${ops}</ul></td>
      <td><strong>${optionLabels[exam.answer]}</strong></td>
      <td>
<form method="post" action="/admin/exams/delete" onsubmit="return confirm('Hapus soal ini?')" style="display:inline;">
  <input type="hidden" name="id" value="${exam.id}">
  <button type="submit">Hapus</button>
</form>
<button onclick='showEditExamForm(${JSON.stringify(exam)})'>Edit</button>

</td>

    `;

    tbody.appendChild(row);
  });
}

function showEditExamForm(exam) {
  const id = exam?.id?.trim?.(); // safe chaining + trim

  if (!id) {
    alert("❌ Soal ini tidak memiliki ID valid. Tidak bisa diedit.");
    console.warn("DEBUG: ID kosong atau invalid →", exam);
    return;
  }

  // Tampilkan form edit
  document.getElementById("exam-edit-form").style.display = "block";
  document.getElementById("exam-form").style.display = "none";
  document.getElementById("exam-list").style.display = "none";

  // Isi semua field dengan data dari soal
  document.getElementById("exam-edit-id").value = id;
  document.getElementById("edit-level").value = exam.level || "";
  document.getElementById("edit-question").value = exam.question || "";

  const [a, b, c, d] = exam.options || [];
  document.getElementById("edit-option-a").value = a || "";
  document.getElementById("edit-option-b").value = b || "";
  document.getElementById("edit-option-c").value = c || "";
  document.getElementById("edit-option-d").value = d || "";

  document.getElementById("edit-answer").value = exam.answer ?? "";
}

function cancelEditExam() {
  document.getElementById("exam-edit-form").style.display = "none";
  document.getElementById("exam-list").style.display = "block";
}

function fillEditForm(exam) {
  document.getElementById("exam-edit-form").style.display = "block";

  document.getElementById("edit-id").value = exam.id;
  document.getElementById("edit-level").value = exam.level;
  document.getElementById("edit-question").value = exam.question;

  document.getElementById("edit-option-a").value = exam.options[0] || "";
  document.getElementById("edit-option-b").value = exam.options[1] || "";
  document.getElementById("edit-option-c").value = exam.options[2] || "";
  document.getElementById("edit-option-d").value = exam.options[3] || "";

  document.getElementById("edit-answer").value = exam.answer;
}

function toggleAddModul() {
  document.getElementById("modul-form-section").style.display = "block";
  document.getElementById("modul-list-section").style.display = "none";
  document.getElementById("modul-edit-section").style.display = "none";
}
function toggleListModul() {
  document.getElementById("modul-form-section").style.display = "none";
  document.getElementById("modul-list-section").style.display = "block";
  document.getElementById("modul-edit-section").style.display = "none";
}
function showEditForm(id, level, title, video_url) {
  toggleAddModul();
  document.getElementById("modul-form-section").style.display = "none";
  document.getElementById("modul-list-section").style.display = "none";
  document.getElementById("modul-edit-section").style.display = "block";

  document.getElementById("edit-id").value = id;
  document.getElementById("edit-level").value = level;
  document.getElementById("edit-title").value = title;
  document.getElementById("edit-video_url").value = video_url;
}
function cancelEdit() {
  toggleListModul();
}