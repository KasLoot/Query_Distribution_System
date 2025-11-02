document.addEventListener("DOMContentLoaded", function () {

  let tasks = {};
  let calendar; // 全域變數方便重整

  // 初始化 FullCalendar
  function initCalendar() {
    const calendarEl = document.getElementById('calendar');
    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'timeGridWeek',
      locale: 'zh-tw',
      allDaySlot: false,
      slotMinTime: "08:00:00",
      slotMaxTime: "20:00:00",
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
      eventDisplay: 'block',
      events: []
    });
    calendar.render();
  }

  // 設定顏色依照 priority
  function getColor(priority) {
    switch (priority) {
      case "High": return "#ff7675";
      case "Medium": return "#fdcb6e";
      case "Low": return "#55efc4";
      default: return "#dfe6e9";
    }
  }

  // 顯示任務在日曆上
  function showPersonTasks(person) {
    if (!tasks[person]) return;
    const userTasks = tasks[person].map(task => ({
      title: task.title,
      start: task.start,
      end: task.end,
      color: getColor(task.priority)
    }));
    calendar.removeAllEvents();
    calendar.addEventSource(userTasks);
  }

  // 建立員工下拉選單
  function buildDropdown() {
    const dropdown = document.getElementById("personDropdown");
    dropdown.innerHTML = "";
    Object.keys(tasks).forEach(person => {
      const option = document.createElement("option");
      option.value = person;
      option.textContent = person;
      dropdown.appendChild(option);
    });
    dropdown.addEventListener("change", (e) => {
      showPersonTasks(e.target.value);
    });

    // 預設顯示第一位員工
    dropdown.value = Object.keys(tasks)[0];
    dropdown.dispatchEvent(new Event('change'));
  }

  // 讀取 schedule.json
  async function loadTasks() {
    try {
      const res = await fetch("./schedule.json?cache=" + Date.now());
      if (!res.ok) throw new Error("無法讀取 JSON");
      tasks = await res.json();
      console.log("✅ schedule.json 已載入");

      if (!calendar) {
        initCalendar();
        buildDropdown();
      }
      const dropdown = document.getElementById("personDropdown");
      showPersonTasks(dropdown.value || Object.keys(tasks)[0]);
    } catch (err) {
      console.error("讀取任務時發生錯誤：", err);
    }
  }

  // 🚀 初次載入
  loadTasks();

  // 🔁 每 5 秒自動重新載入一次
  setInterval(async () => {
    console.log("🔄 檢查是否有新排程...");
    await loadTasks();
  }, 5000);
});