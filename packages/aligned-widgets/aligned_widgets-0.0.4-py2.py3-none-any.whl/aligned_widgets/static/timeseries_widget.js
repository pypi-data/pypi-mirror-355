// frontend/templates/timeseries_widget.html
var timeseries_widget_default = '<div class="widget timeseries-widget">\n  <div class="header">\n    <span class="title" id="title"></span>\n    <div class="legend" id="legend"></div>\n  </div>\n  <div class="graph" id="canvas-holder">\n    <canvas id="canvas"></canvas>\n  </div>\n  <div class="controls">\n    <div class="left">\n      <div>\n        <button id="btnAdd"></button>\n        <button id="btnDelete"></button>\n      </div>\n      <div class="dropdown">\n        <button class="dropbtn" id="btnToggleTagsList">\n          Edit Tags\n        </button>\n        <div id="tagsList" class="dropdown-content"></div>\n      </div>\n    </div>\n    <div class="right">\n      <button id="btnZoomIn"></button>\n      <button id="btnZoomOut"></button>\n    </div>\n  </div>\n</div>\n';

// frontend/timeseries_widget.ts
var TimeseriesWidget = class {
  constructor({ model, el }) {
    this.tagInputElements = [];
    this.lastAnimationFrameTimestamp = null;
    this.animationFrameRequestId = null;
    this.values = [];
    this.annotations = [];
    this.tags = [];
    this.windowSizeInSec = 5;
    this.selectedAnnIndex = null;
    this.selectedResizingHandle = null;
    this.selectedMoveHandle = null;
    this.model = model;
    this.el = el;
    el.innerHTML = timeseries_widget_default;
    this.canvas = el.querySelector("#canvas");
    this.canvas.addEventListener("mousedown", this.canvasMouseDown.bind(this));
    this.canvas.addEventListener("mousemove", this.canvasMouseMove.bind(this));
    this.canvas.addEventListener("mouseup", this.canvasMouseUp.bind(this));
    this.btnAdd = el.querySelector("#btnAdd");
    this.btnAdd.innerHTML = this.model.get("icons").add;
    this.btnAdd.addEventListener("click", this.btnAddClicked.bind(this));
    this.btnDelete = el.querySelector("#btnDelete");
    this.btnDelete.innerHTML = this.model.get("icons").delete;
    this.btnDelete.addEventListener("click", this.btnDeleteClicked.bind(this));
    this.btnZoomIn = el.querySelector("#btnZoomIn");
    this.btnZoomIn.innerHTML = this.model.get("icons").zoom_in;
    this.btnZoomIn.addEventListener("click", this.btnZoomInClicked.bind(this));
    this.btnZoomOut = el.querySelector("#btnZoomOut");
    this.btnZoomOut.innerHTML = this.model.get("icons").zoom_out;
    this.btnZoomOut.addEventListener(
      "click",
      this.btnZoomOutClicked.bind(this)
    );
    this.btnToggleTagsList = el.querySelector("#btnToggleTagsList");
    this.btnToggleTagsList.addEventListener(
      "click",
      this.toggleTagsList.bind(this)
    );
    this.tagsList = el.querySelector("#tagsList");
    this.currentTime = this.model.get("sync_time");
    const times_bytes = this.model.get("times");
    const times_buffer = times_bytes.buffer || times_bytes;
    this.times = new Float64Array(times_buffer);
    const values_bytes = this.model.get("values");
    const values_buffer = values_bytes.buffer || values_bytes;
    const all_values = new Float64Array(values_buffer);
    const num_elements = this.times.length;
    const total_values_count = all_values.length;
    this.numChannels = total_values_count / num_elements;
    for (let i = 0; i < this.numChannels; i++) {
      this.values.push(
        all_values.slice(i * num_elements, i * num_elements + num_elements)
      );
    }
    this.annotations = this.model.get("annotations");
    this.yRange = this.model.get("y_range");
    this.windowSizeInSec = this.model.get("x_range");
    this.tags = this.model.get("tags");
    this.populateTagsList();
    this.addLegend();
    this.addTitle();
  }
  populateTagsList() {
    for (let i = 0; i < this.tags.length; i++) {
      const tag = this.tags[i];
      const label = document.createElement("label");
      const inputCheckbox = document.createElement("input");
      const labelText = document.createTextNode(tag);
      inputCheckbox.type = "checkbox";
      inputCheckbox.value = tag;
      inputCheckbox.style.setProperty("--checkbox-color", this.getTagColor(i));
      inputCheckbox.addEventListener("change", this.tagToggled.bind(this));
      label.appendChild(inputCheckbox);
      label.appendChild(labelText);
      this.tagInputElements.push(inputCheckbox);
      this.tagsList.appendChild(label);
    }
  }
  tagToggled(e) {
    if (this.selectedAnnIndex == null) return;
    const target = e.target;
    const ann = this.annotations[this.selectedAnnIndex];
    if (target.checked) {
      ann.tags.push(target.value);
    } else {
      ann.tags = ann.tags.filter((t) => t !== target.value);
    }
    this.syncAnnotations();
  }
  canvasMouseDown(e) {
    if (this.checkForHandleSelection(e.offsetX)) {
      return;
    }
    if (this.checkForAnnSelection(e.offsetX)) {
      this.updateTagCheckboxes();
      this.btnToggleTagsList.classList.add("show");
    } else {
      this.btnToggleTagsList.classList.remove("show");
      this.tagsList.classList.remove("show");
    }
  }
  updateTagCheckboxes() {
    if (this.selectedAnnIndex == null) return;
    const tags = this.annotations[this.selectedAnnIndex].tags;
    for (const checkbox of this.tagInputElements) {
      checkbox.checked = tags.includes(checkbox.value);
    }
  }
  canvasMouseMove(e) {
    if (this.selectedResizingHandle != null) {
      this.resizeAnnotation(e.offsetX);
    } else if (this.selectedMoveHandle != null) {
      this.moveAnnotation(e.offsetX);
    }
  }
  resizeAnnotation(mouseX) {
    if (this.selectedResizingHandle == null) return;
    const width = this.canvas.width;
    const time = this.currentTime + this.windowSizeInSec * (mouseX - width / 2) / width;
    if (this.selectedResizingHandle.side == "left") {
      this.annotations[this.selectedResizingHandle.annIndex].start = time;
    } else {
      this.annotations[this.selectedResizingHandle.annIndex].end = time;
    }
  }
  moveAnnotation(mouseX) {
    if (this.selectedMoveHandle == null) return;
    const width = this.canvas.width;
    const offsetTime = this.windowSizeInSec * (mouseX - this.selectedMoveHandle.grabX) / width;
    this.annotations[this.selectedMoveHandle.annIndex].start = this.selectedMoveHandle.annStart + offsetTime;
    this.annotations[this.selectedMoveHandle.annIndex].end = this.selectedMoveHandle.annEnd + offsetTime;
  }
  canvasMouseUp() {
    this.selectedResizingHandle = null;
    this.selectedMoveHandle = null;
    this.syncAnnotations();
  }
  btnAddClicked() {
    this.annotations.push({
      start: this.currentTime,
      end: this.currentTime + 0.5,
      tags: []
    });
    this.selectedAnnIndex = this.annotations.length - 1;
    this.syncAnnotations();
  }
  btnDeleteClicked() {
    if (this.selectedAnnIndex == null) return;
    this.annotations.splice(this.selectedAnnIndex, 1);
    this.selectedAnnIndex = null;
    this.syncAnnotations();
  }
  btnZoomInClicked() {
    this.windowSizeInSec = Math.max(0, this.windowSizeInSec - 0.5);
    console.log("zoomIn", this.windowSizeInSec);
  }
  btnZoomOutClicked() {
    this.windowSizeInSec += 0.5;
    console.log("zoomOut", this.windowSizeInSec);
  }
  toggleTagsList() {
    this.tagsList.classList.toggle("show");
  }
  syncAnnotations() {
    this.model.set("annotations", []);
    this.model.set("annotations", [...this.annotations]);
    this.model.save_changes();
  }
  checkForAnnSelection(mouseX) {
    const startTime = this.currentTime - this.windowSizeInSec / 2;
    const endTime = this.currentTime + this.windowSizeInSec / 2;
    const drawnAnns = this.getAnnotationsToDraw(startTime, endTime);
    this.selectedAnnIndex = null;
    for (let i = 0; i < drawnAnns.length; i++) {
      const ann = drawnAnns[i];
      if (ann.start > mouseX || ann.start + ann.width < mouseX) continue;
      this.selectedAnnIndex = ann.index;
      return true;
    }
    return false;
  }
  checkForHandleSelection(mouseX) {
    const startTime = this.currentTime - this.windowSizeInSec / 2;
    const endTime = this.currentTime + this.windowSizeInSec / 2;
    const drawnAnns = this.getAnnotationsToDraw(startTime, endTime);
    this.selectedResizingHandle = null;
    this.selectedMoveHandle = null;
    for (let i = 0; i < drawnAnns.length; i++) {
      const ann = drawnAnns[i];
      if (Math.abs(mouseX - ann.start) < 6) {
        this.selectedResizingHandle = {
          annIndex: ann.index,
          side: "left"
        };
        return true;
      }
      if (Math.abs(mouseX - ann.start - ann.width) < 6) {
        this.selectedResizingHandle = {
          annIndex: ann.index,
          side: "right"
        };
        return true;
      }
      if (mouseX > ann.start && mouseX < ann.start + ann.width) {
        this.selectedMoveHandle = {
          annIndex: ann.index,
          grabX: mouseX,
          annStart: this.annotations[ann.index].start,
          annEnd: this.annotations[ann.index].end
        };
      }
    }
    return false;
  }
  addLegend() {
    const legend = this.el.querySelector("#legend");
    for (const channel of this.model.get("channel_names")) {
      const channelIndex = this.model.get("channel_names").findIndex((e) => e == channel);
      const label = document.createElement("span");
      label.innerHTML = channel;
      label.style.setProperty("--line-color", this.getPlotColor(channelIndex));
      legend.append(label);
    }
  }
  addTitle() {
    const title = this.el.querySelector("#title");
    title.innerHTML = this.model.get("title");
  }
  getPlotColor(channelIndex) {
    const colors = [
      "#F44336",
      "#4CAF50",
      "#2196F3",
      "#FFEB3B",
      "#795548",
      "#673AB7"
    ];
    const index = channelIndex % colors.length;
    return colors[index];
  }
  getTagColor(tagIndex) {
    const colors = [
      "#F44336",
      "#3F51B5",
      "#00BCD4",
      "#9C27B0",
      "#E91E63",
      "#CDDC39",
      "#795548",
      "#FFEB3B",
      "#607D8B",
      "#2196F3"
    ];
    const index = tagIndex % colors.length;
    return colors[index];
  }
  step(timestamp) {
    if (!this.lastAnimationFrameTimestamp) {
      const canvasHolder = this.el.querySelector("#canvas-holder");
      this.canvas.width = canvasHolder.clientWidth;
      this.canvas.height = canvasHolder.clientHeight;
      this.canvas.style.width = "100%";
      this.canvas.style.height = "100%";
      this.lastAnimationFrameTimestamp = timestamp;
    }
    const delta = timestamp - this.lastAnimationFrameTimestamp;
    this.lastAnimationFrameTimestamp = timestamp;
    if (this.model.get("is_running")) {
      const duration = this.times[this.times.length - 1];
      this.currentTime = Math.min(this.currentTime + delta / 1e3, duration);
    }
    this.clearFrame();
    this.draw();
    this.animationFrameRequestId = requestAnimationFrame(this.step);
  }
  draw() {
    const startTime = this.currentTime - this.windowSizeInSec / 2;
    const endTime = this.currentTime + this.windowSizeInSec / 2;
    const startIndex = this.times.findIndex((e) => e >= startTime);
    const endIndexPlus1 = this.times.findIndex((e) => e > endTime);
    const endIndex = endIndexPlus1 != -1 ? Math.max(endIndexPlus1 - 1, 0) : this.times.length - 1;
    const firstPointTimeDelta = this.times[startIndex] - this.currentTime;
    const lastPointTimeDelta = this.times[endIndex] - this.currentTime;
    const leftOffsetPercentage = Math.max(
      firstPointTimeDelta / this.windowSizeInSec + 0.5,
      0
    );
    const rightOffsetPercentage = lastPointTimeDelta / this.windowSizeInSec + 0.5;
    this.drawAnnotations(startTime, endTime);
    for (let c = 0; c < this.numChannels; c++) {
      this.drawPlot(
        c,
        startIndex,
        endIndex,
        leftOffsetPercentage,
        rightOffsetPercentage
      );
    }
  }
  getRange(startIndex, endIndex) {
    let min = this.yRange.min;
    let max = this.yRange.max;
    if (min != null && max != null) return { min, max };
    const mins = [];
    const maxs = [];
    for (let c = 0; c < this.numChannels; c++) {
      if (min == null) {
        mins.push(Math.min(...this.values[c].slice(startIndex, endIndex + 1)));
      }
      if (max == null) {
        maxs.push(Math.max(...this.values[c].slice(startIndex, endIndex + 1)));
      }
    }
    return {
      min: min ? min : Math.min(...mins),
      max: max ? max : Math.max(...maxs)
    };
  }
  drawPlot(channelIndex, startIndex, endIndex, leftOffsetPercentage, rightOffsetPercentage) {
    if (isNaN(startIndex) || isNaN(endIndex)) return;
    const ctx = this.canvas.getContext("2d");
    const width = this.canvas.width;
    const height = this.canvas.height;
    if (!ctx) {
      console.error("Failed to get 2D context");
      return;
    }
    ctx.strokeStyle = this.getPlotColor(channelIndex);
    ctx.lineWidth = 2;
    ctx.beginPath();
    const indexRange = endIndex - startIndex;
    const fullWidthRange = width;
    const startX = leftOffsetPercentage * fullWidthRange;
    const endX = rightOffsetPercentage * fullWidthRange;
    const widthRange = endX - startX;
    const heightRange = height;
    const { min, max } = this.getRange(startIndex, endIndex);
    const yRange = max - min;
    const values = this.values[channelIndex];
    ctx.moveTo(
      startX,
      height - heightRange * (values[startIndex] - min) / yRange
    );
    const max_points_to_display = width;
    const di = indexRange > max_points_to_display ? Math.floor(indexRange / max_points_to_display) : 1;
    for (let i = Math.max(0, startIndex - di); i < Math.min(values.length, endIndex + 2 * di); i += di) {
      const x = (i - startIndex) / indexRange * widthRange + startX;
      const y = height - heightRange * (values[i] - min) / yRange;
      ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  getAnnotationsToDraw(startTime, endTime) {
    let annotationsToDraw = [];
    const width = this.canvas.width;
    const leftOffsetPercentage = 0;
    const rightOffsetPercentage = 1;
    const fullWidthRange = width;
    const startX = fullWidthRange * leftOffsetPercentage;
    const endX = fullWidthRange * rightOffsetPercentage;
    const widthRange = endX - startX;
    const timeRange = endTime - startTime;
    for (let i = 0; i < this.annotations.length; i++) {
      const ann = this.annotations[i];
      if (ann.start >= startTime && ann.start <= endTime || ann.end >= startTime && ann.end <= endTime || ann.start <= startTime && ann.end >= endTime) {
        const start = widthRange * (Math.max(ann["start"], startTime) - startTime) / timeRange;
        const end = widthRange * (Math.min(ann["end"], endTime) - startTime) / timeRange;
        annotationsToDraw.push({
          start: startX + start,
          width: end - start,
          tagIndexes: ann.tags.map((t) => this.tags.indexOf(t)),
          index: i
        });
      }
    }
    return annotationsToDraw;
  }
  drawAnnotations(startTime, endTime) {
    const ctx = this.canvas.getContext("2d");
    if (!ctx) {
      console.error("Failed to get 2D context");
      return;
    }
    const height = this.canvas.height;
    const indicatorPadding = 2;
    const indicatorHeight = 5;
    const annotationsToDraw = this.getAnnotationsToDraw(startTime, endTime);
    for (let i = 0; i < annotationsToDraw.length; i++) {
      const ann = annotationsToDraw[i];
      ctx.fillStyle = `#78909C${ann.index == this.selectedAnnIndex ? "44" : "22"}`;
      ctx.fillRect(ann.start, 0, ann.width, height);
      for (let i2 = 0; i2 < ann.tagIndexes.length; i2++) {
        ctx.fillStyle = this.getTagColor(ann.tagIndexes[i2]);
        ctx.fillRect(
          ann.start + indicatorPadding,
          indicatorPadding + i2 * indicatorHeight,
          ann.width - 2 * indicatorPadding,
          indicatorHeight - indicatorPadding
        );
      }
      if (this.selectedAnnIndex == ann.index) {
        ctx.lineCap = "round";
        ctx.strokeStyle = "#78909C";
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(ann.start - 4, height / 2 - 12);
        ctx.lineTo(ann.start - 4, height / 2 + 12);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(ann.start + 4, height / 2 - 12);
        ctx.lineTo(ann.start + 4, height / 2 + 12);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(ann.start + ann.width - 4, height / 2 - 12);
        ctx.lineTo(ann.start + ann.width - 4, height / 2 + 12);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(ann.start + ann.width + 4, height / 2 - 12);
        ctx.lineTo(ann.start + ann.width + 4, height / 2 + 12);
        ctx.stroke();
      }
    }
  }
  clearFrame() {
    const ctx = this.canvas.getContext("2d");
    const width = this.canvas.width;
    const height = this.canvas.height;
    if (!ctx) {
      console.error("Failed to get 2D context");
      return;
    }
    ctx.clearRect(0, 0, width, height);
    this.drawAxis(ctx, width, height);
    this.drawXLabels(ctx, width, height);
  }
  drawAxis(ctx, width, height) {
    ctx.strokeStyle = "#607d8b";
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();
  }
  drawXLabels(ctx, width, height) {
    const ticksToDraw = 5;
    const ticksToDrawHalf = Math.floor(ticksToDraw);
    const middleTickTime = this.windowSizeInSec / ticksToDraw * Math.floor(this.currentTime / (this.windowSizeInSec / ticksToDraw));
    ctx.strokeStyle = "#B0BEC5";
    ctx.fillStyle = "#607d8b";
    ctx.font = "12px Arial";
    for (let i = -ticksToDrawHalf; i <= ticksToDrawHalf + 1; i += 1) {
      const tickTime = i * (this.windowSizeInSec / ticksToDraw) + middleTickTime;
      const x = width * (tickTime - this.currentTime) / this.windowSizeInSec;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
      ctx.fillText(
        (tickTime - this.windowSizeInSec / 2).toFixed(2),
        x + 4,
        height - 4
      );
    }
  }
  syncTimeChanged() {
    this.currentTime = this.model.get("sync_time");
  }
  isRunningChanged() {
  }
  render() {
    this.model.on("change:sync_time", this.syncTimeChanged.bind(this));
    this.model.on("change:is_running", this.isRunningChanged.bind(this));
    this.step = this.step.bind(this);
    this.animationFrameRequestId = requestAnimationFrame(this.step);
  }
  destroy() {
    cancelAnimationFrame(this.animationFrameRequestId);
  }
};
var timeseries_widget_default2 = {
  render(props) {
    const widget = new TimeseriesWidget(props);
    widget.render();
    return () => widget.destroy();
  }
};
export {
  timeseries_widget_default2 as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsiLi4vLi4vLi4vZnJvbnRlbmQvdGVtcGxhdGVzL3RpbWVzZXJpZXNfd2lkZ2V0Lmh0bWwiLCAiLi4vLi4vLi4vZnJvbnRlbmQvdGltZXNlcmllc193aWRnZXQudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbIjxkaXYgY2xhc3M9XCJ3aWRnZXQgdGltZXNlcmllcy13aWRnZXRcIj5cbiAgPGRpdiBjbGFzcz1cImhlYWRlclwiPlxuICAgIDxzcGFuIGNsYXNzPVwidGl0bGVcIiBpZD1cInRpdGxlXCI+PC9zcGFuPlxuICAgIDxkaXYgY2xhc3M9XCJsZWdlbmRcIiBpZD1cImxlZ2VuZFwiPjwvZGl2PlxuICA8L2Rpdj5cbiAgPGRpdiBjbGFzcz1cImdyYXBoXCIgaWQ9XCJjYW52YXMtaG9sZGVyXCI+XG4gICAgPGNhbnZhcyBpZD1cImNhbnZhc1wiPjwvY2FudmFzPlxuICA8L2Rpdj5cbiAgPGRpdiBjbGFzcz1cImNvbnRyb2xzXCI+XG4gICAgPGRpdiBjbGFzcz1cImxlZnRcIj5cbiAgICAgIDxkaXY+XG4gICAgICAgIDxidXR0b24gaWQ9XCJidG5BZGRcIj48L2J1dHRvbj5cbiAgICAgICAgPGJ1dHRvbiBpZD1cImJ0bkRlbGV0ZVwiPjwvYnV0dG9uPlxuICAgICAgPC9kaXY+XG4gICAgICA8ZGl2IGNsYXNzPVwiZHJvcGRvd25cIj5cbiAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImRyb3BidG5cIiBpZD1cImJ0blRvZ2dsZVRhZ3NMaXN0XCI+XG4gICAgICAgICAgRWRpdCBUYWdzXG4gICAgICAgIDwvYnV0dG9uPlxuICAgICAgICA8ZGl2IGlkPVwidGFnc0xpc3RcIiBjbGFzcz1cImRyb3Bkb3duLWNvbnRlbnRcIj48L2Rpdj5cbiAgICAgIDwvZGl2PlxuICAgIDwvZGl2PlxuICAgIDxkaXYgY2xhc3M9XCJyaWdodFwiPlxuICAgICAgPGJ1dHRvbiBpZD1cImJ0blpvb21JblwiPjwvYnV0dG9uPlxuICAgICAgPGJ1dHRvbiBpZD1cImJ0blpvb21PdXRcIj48L2J1dHRvbj5cbiAgICA8L2Rpdj5cbiAgPC9kaXY+XG48L2Rpdj5cbiIsICJpbXBvcnQgdHlwZSB7IEFueU1vZGVsLCBSZW5kZXJQcm9wcyB9IGZyb20gJ0Bhbnl3aWRnZXQvdHlwZXMnO1xuaW1wb3J0ICcuL3N0eWxlcy93aWRnZXQuY3NzJztcbmltcG9ydCAnLi9zdHlsZXMvdGltZXNlcmllc193aWRnZXQuY3NzJztcbmltcG9ydCB0aW1lc2VyaWVzVGVtcGxhdGUgZnJvbSAnLi90ZW1wbGF0ZXMvdGltZXNlcmllc193aWRnZXQuaHRtbCc7XG5cbnR5cGUgQW5ub3RhdGlvbiA9IHtcbiAgc3RhcnQ6IG51bWJlcjtcbiAgZW5kOiBudW1iZXI7XG4gIHRhZ3M6IHN0cmluZ1tdO1xufTtcblxudHlwZSBZUmFuZ2UgPSB7XG4gIG1pbjogbnVtYmVyIHwgbnVsbDtcbiAgbWF4OiBudW1iZXIgfCBudWxsO1xufTtcblxuaW50ZXJmYWNlIFRpbWVyc2VyaWVzV2lkZ2V0TW9kZWwge1xuICBpc19ydW5uaW5nOiBib29sZWFuO1xuICBzeW5jX3RpbWU6IG51bWJlcjtcbiAgdGltZXM6IEZsb2F0NjRBcnJheTtcbiAgdmFsdWVzOiBGbG9hdDY0QXJyYXk7XG4gIHRhZ3M6IHN0cmluZ1tdO1xuICBhbm5vdGF0aW9uczogQW5ub3RhdGlvbltdO1xuICBjaGFubmVsX25hbWVzOiBzdHJpbmdbXTtcbiAgdGl0bGU6IHN0cmluZztcbiAgeV9yYW5nZTogWVJhbmdlO1xuICB4X3JhbmdlOiBudW1iZXI7XG4gIGljb25zOiB7XG4gICAgYWRkOiBzdHJpbmc7XG4gICAgZGVsZXRlOiBzdHJpbmc7XG4gICAgem9vbV9pbjogc3RyaW5nO1xuICAgIHpvb21fb3V0OiBzdHJpbmc7XG4gIH07XG59XG5cbmNsYXNzIFRpbWVzZXJpZXNXaWRnZXQge1xuICBlbDogSFRNTEVsZW1lbnQ7XG4gIG1vZGVsOiBBbnlNb2RlbDxUaW1lcnNlcmllc1dpZGdldE1vZGVsPjtcblxuICBjYW52YXM6IEhUTUxDYW52YXNFbGVtZW50O1xuICBidG5BZGQ6IEhUTUxCdXR0b25FbGVtZW50O1xuICBidG5EZWxldGU6IEhUTUxCdXR0b25FbGVtZW50O1xuICBidG5ab29tSW46IEhUTUxCdXR0b25FbGVtZW50O1xuICBidG5ab29tT3V0OiBIVE1MQnV0dG9uRWxlbWVudDtcbiAgYnRuVG9nZ2xlVGFnc0xpc3Q6IEhUTUxCdXR0b25FbGVtZW50O1xuICB0YWdzTGlzdDogSFRNTERpdkVsZW1lbnQ7XG4gIHRhZ0lucHV0RWxlbWVudHM6IEhUTUxJbnB1dEVsZW1lbnRbXSA9IFtdO1xuXG4gIGN1cnJlbnRUaW1lOiBudW1iZXI7XG4gIGxhc3RBbmltYXRpb25GcmFtZVRpbWVzdGFtcDogRE9NSGlnaFJlc1RpbWVTdGFtcCB8IG51bGwgPSBudWxsO1xuICBhbmltYXRpb25GcmFtZVJlcXVlc3RJZDogbnVtYmVyIHwgbnVsbCA9IG51bGw7XG5cbiAgdGltZXM6IEZsb2F0NjRBcnJheTtcbiAgdmFsdWVzOiBGbG9hdDY0QXJyYXlbXSA9IFtdO1xuICBudW1DaGFubmVsczogbnVtYmVyO1xuICB5UmFuZ2U6IFlSYW5nZTtcbiAgYW5ub3RhdGlvbnM6IEFubm90YXRpb25bXSA9IFtdO1xuICB0YWdzOiBzdHJpbmdbXSA9IFtdO1xuXG4gIHdpbmRvd1NpemVJblNlYyA9IDU7XG4gIHNlbGVjdGVkQW5uSW5kZXg6IG51bWJlciB8IG51bGwgPSBudWxsO1xuICBzZWxlY3RlZFJlc2l6aW5nSGFuZGxlOiB7XG4gICAgYW5uSW5kZXg6IG51bWJlcjtcbiAgICBzaWRlOiAnbGVmdCcgfCAncmlnaHQnO1xuICB9IHwgbnVsbCA9IG51bGw7XG4gIHNlbGVjdGVkTW92ZUhhbmRsZToge1xuICAgIGFubkluZGV4OiBudW1iZXI7XG4gICAgZ3JhYlg6IG51bWJlcjtcbiAgICBhbm5TdGFydDogbnVtYmVyO1xuICAgIGFubkVuZDogbnVtYmVyO1xuICB9IHwgbnVsbCA9IG51bGw7XG5cbiAgY29uc3RydWN0b3IoeyBtb2RlbCwgZWwgfTogUmVuZGVyUHJvcHM8VGltZXJzZXJpZXNXaWRnZXRNb2RlbD4pIHtcbiAgICB0aGlzLm1vZGVsID0gbW9kZWw7XG4gICAgdGhpcy5lbCA9IGVsO1xuICAgIGVsLmlubmVySFRNTCA9IHRpbWVzZXJpZXNUZW1wbGF0ZTtcblxuICAgIHRoaXMuY2FudmFzID0gZWwucXVlcnlTZWxlY3RvcignI2NhbnZhcycpITtcbiAgICB0aGlzLmNhbnZhcy5hZGRFdmVudExpc3RlbmVyKCdtb3VzZWRvd24nLCB0aGlzLmNhbnZhc01vdXNlRG93bi5iaW5kKHRoaXMpKTtcbiAgICB0aGlzLmNhbnZhcy5hZGRFdmVudExpc3RlbmVyKCdtb3VzZW1vdmUnLCB0aGlzLmNhbnZhc01vdXNlTW92ZS5iaW5kKHRoaXMpKTtcbiAgICB0aGlzLmNhbnZhcy5hZGRFdmVudExpc3RlbmVyKCdtb3VzZXVwJywgdGhpcy5jYW52YXNNb3VzZVVwLmJpbmQodGhpcykpO1xuXG4gICAgdGhpcy5idG5BZGQgPSBlbC5xdWVyeVNlbGVjdG9yKCcjYnRuQWRkJykhO1xuICAgIHRoaXMuYnRuQWRkLmlubmVySFRNTCA9IHRoaXMubW9kZWwuZ2V0KCdpY29ucycpLmFkZDtcbiAgICB0aGlzLmJ0bkFkZC5hZGRFdmVudExpc3RlbmVyKCdjbGljaycsIHRoaXMuYnRuQWRkQ2xpY2tlZC5iaW5kKHRoaXMpKTtcblxuICAgIHRoaXMuYnRuRGVsZXRlID0gZWwucXVlcnlTZWxlY3RvcignI2J0bkRlbGV0ZScpITtcbiAgICB0aGlzLmJ0bkRlbGV0ZS5pbm5lckhUTUwgPSB0aGlzLm1vZGVsLmdldCgnaWNvbnMnKS5kZWxldGU7XG4gICAgdGhpcy5idG5EZWxldGUuYWRkRXZlbnRMaXN0ZW5lcignY2xpY2snLCB0aGlzLmJ0bkRlbGV0ZUNsaWNrZWQuYmluZCh0aGlzKSk7XG5cbiAgICB0aGlzLmJ0blpvb21JbiA9IGVsLnF1ZXJ5U2VsZWN0b3IoJyNidG5ab29tSW4nKSE7XG4gICAgdGhpcy5idG5ab29tSW4uaW5uZXJIVE1MID0gdGhpcy5tb2RlbC5nZXQoJ2ljb25zJykuem9vbV9pbjtcbiAgICB0aGlzLmJ0blpvb21Jbi5hZGRFdmVudExpc3RlbmVyKCdjbGljaycsIHRoaXMuYnRuWm9vbUluQ2xpY2tlZC5iaW5kKHRoaXMpKTtcblxuICAgIHRoaXMuYnRuWm9vbU91dCA9IGVsLnF1ZXJ5U2VsZWN0b3IoJyNidG5ab29tT3V0JykhO1xuICAgIHRoaXMuYnRuWm9vbU91dC5pbm5lckhUTUwgPSB0aGlzLm1vZGVsLmdldCgnaWNvbnMnKS56b29tX291dDtcbiAgICB0aGlzLmJ0blpvb21PdXQuYWRkRXZlbnRMaXN0ZW5lcihcbiAgICAgICdjbGljaycsXG4gICAgICB0aGlzLmJ0blpvb21PdXRDbGlja2VkLmJpbmQodGhpcylcbiAgICApO1xuXG4gICAgdGhpcy5idG5Ub2dnbGVUYWdzTGlzdCA9IGVsLnF1ZXJ5U2VsZWN0b3IoJyNidG5Ub2dnbGVUYWdzTGlzdCcpITtcbiAgICB0aGlzLmJ0blRvZ2dsZVRhZ3NMaXN0LmFkZEV2ZW50TGlzdGVuZXIoXG4gICAgICAnY2xpY2snLFxuICAgICAgdGhpcy50b2dnbGVUYWdzTGlzdC5iaW5kKHRoaXMpXG4gICAgKTtcblxuICAgIHRoaXMudGFnc0xpc3QgPSBlbC5xdWVyeVNlbGVjdG9yKCcjdGFnc0xpc3QnKSE7XG5cbiAgICB0aGlzLmN1cnJlbnRUaW1lID0gdGhpcy5tb2RlbC5nZXQoJ3N5bmNfdGltZScpO1xuXG4gICAgY29uc3QgdGltZXNfYnl0ZXMgPSB0aGlzLm1vZGVsLmdldCgndGltZXMnKTtcbiAgICBjb25zdCB0aW1lc19idWZmZXIgPSB0aW1lc19ieXRlcy5idWZmZXIgfHwgdGltZXNfYnl0ZXM7XG4gICAgdGhpcy50aW1lcyA9IG5ldyBGbG9hdDY0QXJyYXkodGltZXNfYnVmZmVyKTtcblxuICAgIGNvbnN0IHZhbHVlc19ieXRlcyA9IHRoaXMubW9kZWwuZ2V0KCd2YWx1ZXMnKTtcbiAgICBjb25zdCB2YWx1ZXNfYnVmZmVyID0gdmFsdWVzX2J5dGVzLmJ1ZmZlciB8fCB2YWx1ZXNfYnl0ZXM7XG4gICAgY29uc3QgYWxsX3ZhbHVlcyA9IG5ldyBGbG9hdDY0QXJyYXkodmFsdWVzX2J1ZmZlcik7XG5cbiAgICBjb25zdCBudW1fZWxlbWVudHMgPSB0aGlzLnRpbWVzLmxlbmd0aDtcbiAgICBjb25zdCB0b3RhbF92YWx1ZXNfY291bnQgPSBhbGxfdmFsdWVzLmxlbmd0aDtcbiAgICB0aGlzLm51bUNoYW5uZWxzID0gdG90YWxfdmFsdWVzX2NvdW50IC8gbnVtX2VsZW1lbnRzO1xuXG4gICAgZm9yIChsZXQgaSA9IDA7IGkgPCB0aGlzLm51bUNoYW5uZWxzOyBpKyspIHtcbiAgICAgIHRoaXMudmFsdWVzLnB1c2goXG4gICAgICAgIGFsbF92YWx1ZXMuc2xpY2UoaSAqIG51bV9lbGVtZW50cywgaSAqIG51bV9lbGVtZW50cyArIG51bV9lbGVtZW50cylcbiAgICAgICk7XG4gICAgfVxuXG4gICAgdGhpcy5hbm5vdGF0aW9ucyA9IHRoaXMubW9kZWwuZ2V0KCdhbm5vdGF0aW9ucycpO1xuICAgIHRoaXMueVJhbmdlID0gdGhpcy5tb2RlbC5nZXQoJ3lfcmFuZ2UnKTtcbiAgICB0aGlzLndpbmRvd1NpemVJblNlYyA9IHRoaXMubW9kZWwuZ2V0KCd4X3JhbmdlJyk7XG4gICAgdGhpcy50YWdzID0gdGhpcy5tb2RlbC5nZXQoJ3RhZ3MnKTtcblxuICAgIHRoaXMucG9wdWxhdGVUYWdzTGlzdCgpO1xuICAgIHRoaXMuYWRkTGVnZW5kKCk7XG4gICAgdGhpcy5hZGRUaXRsZSgpO1xuICB9XG5cbiAgcG9wdWxhdGVUYWdzTGlzdCgpIHtcbiAgICBmb3IgKGxldCBpID0gMDsgaSA8IHRoaXMudGFncy5sZW5ndGg7IGkrKykge1xuICAgICAgY29uc3QgdGFnID0gdGhpcy50YWdzW2ldO1xuXG4gICAgICBjb25zdCBsYWJlbCA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ2xhYmVsJyk7XG4gICAgICBjb25zdCBpbnB1dENoZWNrYm94ID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgnaW5wdXQnKTtcbiAgICAgIGNvbnN0IGxhYmVsVGV4dCA9IGRvY3VtZW50LmNyZWF0ZVRleHROb2RlKHRhZyk7XG5cbiAgICAgIGlucHV0Q2hlY2tib3gudHlwZSA9ICdjaGVja2JveCc7XG4gICAgICBpbnB1dENoZWNrYm94LnZhbHVlID0gdGFnO1xuICAgICAgaW5wdXRDaGVja2JveC5zdHlsZS5zZXRQcm9wZXJ0eSgnLS1jaGVja2JveC1jb2xvcicsIHRoaXMuZ2V0VGFnQ29sb3IoaSkpO1xuICAgICAgaW5wdXRDaGVja2JveC5hZGRFdmVudExpc3RlbmVyKCdjaGFuZ2UnLCB0aGlzLnRhZ1RvZ2dsZWQuYmluZCh0aGlzKSk7XG5cbiAgICAgIGxhYmVsLmFwcGVuZENoaWxkKGlucHV0Q2hlY2tib3gpO1xuICAgICAgbGFiZWwuYXBwZW5kQ2hpbGQobGFiZWxUZXh0KTtcblxuICAgICAgdGhpcy50YWdJbnB1dEVsZW1lbnRzLnB1c2goaW5wdXRDaGVja2JveCk7XG4gICAgICB0aGlzLnRhZ3NMaXN0LmFwcGVuZENoaWxkKGxhYmVsKTtcbiAgICB9XG4gIH1cblxuICB0YWdUb2dnbGVkKGU6IEV2ZW50KSB7XG4gICAgaWYgKHRoaXMuc2VsZWN0ZWRBbm5JbmRleCA9PSBudWxsKSByZXR1cm47XG5cbiAgICBjb25zdCB0YXJnZXQgPSBlLnRhcmdldCBhcyBIVE1MSW5wdXRFbGVtZW50O1xuICAgIGNvbnN0IGFubiA9IHRoaXMuYW5ub3RhdGlvbnNbdGhpcy5zZWxlY3RlZEFubkluZGV4XTtcblxuICAgIGlmICh0YXJnZXQuY2hlY2tlZCkge1xuICAgICAgYW5uLnRhZ3MucHVzaCh0YXJnZXQudmFsdWUpO1xuICAgIH0gZWxzZSB7XG4gICAgICBhbm4udGFncyA9IGFubi50YWdzLmZpbHRlcih0ID0+IHQgIT09IHRhcmdldC52YWx1ZSk7XG4gICAgfVxuXG4gICAgdGhpcy5zeW5jQW5ub3RhdGlvbnMoKTtcbiAgfVxuXG4gIGNhbnZhc01vdXNlRG93bihlOiBNb3VzZUV2ZW50KSB7XG4gICAgaWYgKHRoaXMuY2hlY2tGb3JIYW5kbGVTZWxlY3Rpb24oZS5vZmZzZXRYKSkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIGlmICh0aGlzLmNoZWNrRm9yQW5uU2VsZWN0aW9uKGUub2Zmc2V0WCkpIHtcbiAgICAgIHRoaXMudXBkYXRlVGFnQ2hlY2tib3hlcygpO1xuICAgICAgdGhpcy5idG5Ub2dnbGVUYWdzTGlzdC5jbGFzc0xpc3QuYWRkKCdzaG93Jyk7XG4gICAgfSBlbHNlIHtcbiAgICAgIHRoaXMuYnRuVG9nZ2xlVGFnc0xpc3QuY2xhc3NMaXN0LnJlbW92ZSgnc2hvdycpO1xuICAgICAgdGhpcy50YWdzTGlzdC5jbGFzc0xpc3QucmVtb3ZlKCdzaG93Jyk7XG4gICAgfVxuICB9XG5cbiAgdXBkYXRlVGFnQ2hlY2tib3hlcygpIHtcbiAgICBpZiAodGhpcy5zZWxlY3RlZEFubkluZGV4ID09IG51bGwpIHJldHVybjtcbiAgICBjb25zdCB0YWdzID0gdGhpcy5hbm5vdGF0aW9uc1t0aGlzLnNlbGVjdGVkQW5uSW5kZXhdLnRhZ3M7XG5cbiAgICBmb3IgKGNvbnN0IGNoZWNrYm94IG9mIHRoaXMudGFnSW5wdXRFbGVtZW50cykge1xuICAgICAgY2hlY2tib3guY2hlY2tlZCA9IHRhZ3MuaW5jbHVkZXMoY2hlY2tib3gudmFsdWUpO1xuICAgIH1cbiAgfVxuXG4gIGNhbnZhc01vdXNlTW92ZShlOiBNb3VzZUV2ZW50KSB7XG4gICAgaWYgKHRoaXMuc2VsZWN0ZWRSZXNpemluZ0hhbmRsZSAhPSBudWxsKSB7XG4gICAgICB0aGlzLnJlc2l6ZUFubm90YXRpb24oZS5vZmZzZXRYKTtcbiAgICB9IGVsc2UgaWYgKHRoaXMuc2VsZWN0ZWRNb3ZlSGFuZGxlICE9IG51bGwpIHtcbiAgICAgIHRoaXMubW92ZUFubm90YXRpb24oZS5vZmZzZXRYKTtcbiAgICB9XG4gIH1cblxuICByZXNpemVBbm5vdGF0aW9uKG1vdXNlWDogbnVtYmVyKSB7XG4gICAgaWYgKHRoaXMuc2VsZWN0ZWRSZXNpemluZ0hhbmRsZSA9PSBudWxsKSByZXR1cm47XG5cbiAgICBjb25zdCB3aWR0aCA9IHRoaXMuY2FudmFzLndpZHRoO1xuICAgIGNvbnN0IHRpbWUgPVxuICAgICAgdGhpcy5jdXJyZW50VGltZSArICh0aGlzLndpbmRvd1NpemVJblNlYyAqIChtb3VzZVggLSB3aWR0aCAvIDIpKSAvIHdpZHRoO1xuXG4gICAgaWYgKHRoaXMuc2VsZWN0ZWRSZXNpemluZ0hhbmRsZS5zaWRlID09ICdsZWZ0Jykge1xuICAgICAgdGhpcy5hbm5vdGF0aW9uc1t0aGlzLnNlbGVjdGVkUmVzaXppbmdIYW5kbGUuYW5uSW5kZXhdLnN0YXJ0ID0gdGltZTtcbiAgICB9IGVsc2Uge1xuICAgICAgdGhpcy5hbm5vdGF0aW9uc1t0aGlzLnNlbGVjdGVkUmVzaXppbmdIYW5kbGUuYW5uSW5kZXhdLmVuZCA9IHRpbWU7XG4gICAgfVxuICB9XG5cbiAgbW92ZUFubm90YXRpb24obW91c2VYOiBudW1iZXIpIHtcbiAgICBpZiAodGhpcy5zZWxlY3RlZE1vdmVIYW5kbGUgPT0gbnVsbCkgcmV0dXJuO1xuXG4gICAgY29uc3Qgd2lkdGggPSB0aGlzLmNhbnZhcy53aWR0aDtcbiAgICBjb25zdCBvZmZzZXRUaW1lID1cbiAgICAgICh0aGlzLndpbmRvd1NpemVJblNlYyAqIChtb3VzZVggLSB0aGlzLnNlbGVjdGVkTW92ZUhhbmRsZS5ncmFiWCkpIC8gd2lkdGg7XG4gICAgdGhpcy5hbm5vdGF0aW9uc1t0aGlzLnNlbGVjdGVkTW92ZUhhbmRsZS5hbm5JbmRleF0uc3RhcnQgPVxuICAgICAgdGhpcy5zZWxlY3RlZE1vdmVIYW5kbGUuYW5uU3RhcnQgKyBvZmZzZXRUaW1lO1xuICAgIHRoaXMuYW5ub3RhdGlvbnNbdGhpcy5zZWxlY3RlZE1vdmVIYW5kbGUuYW5uSW5kZXhdLmVuZCA9XG4gICAgICB0aGlzLnNlbGVjdGVkTW92ZUhhbmRsZS5hbm5FbmQgKyBvZmZzZXRUaW1lO1xuICB9XG5cbiAgY2FudmFzTW91c2VVcCgpIHtcbiAgICB0aGlzLnNlbGVjdGVkUmVzaXppbmdIYW5kbGUgPSBudWxsO1xuICAgIHRoaXMuc2VsZWN0ZWRNb3ZlSGFuZGxlID0gbnVsbDtcbiAgICB0aGlzLnN5bmNBbm5vdGF0aW9ucygpO1xuICB9XG5cbiAgYnRuQWRkQ2xpY2tlZCgpIHtcbiAgICB0aGlzLmFubm90YXRpb25zLnB1c2goe1xuICAgICAgc3RhcnQ6IHRoaXMuY3VycmVudFRpbWUsXG4gICAgICBlbmQ6IHRoaXMuY3VycmVudFRpbWUgKyAwLjUsXG4gICAgICB0YWdzOiBbXSxcbiAgICB9KTtcblxuICAgIHRoaXMuc2VsZWN0ZWRBbm5JbmRleCA9IHRoaXMuYW5ub3RhdGlvbnMubGVuZ3RoIC0gMTtcblxuICAgIHRoaXMuc3luY0Fubm90YXRpb25zKCk7XG4gIH1cblxuICBidG5EZWxldGVDbGlja2VkKCkge1xuICAgIGlmICh0aGlzLnNlbGVjdGVkQW5uSW5kZXggPT0gbnVsbCkgcmV0dXJuO1xuXG4gICAgdGhpcy5hbm5vdGF0aW9ucy5zcGxpY2UodGhpcy5zZWxlY3RlZEFubkluZGV4LCAxKTtcbiAgICB0aGlzLnNlbGVjdGVkQW5uSW5kZXggPSBudWxsO1xuXG4gICAgdGhpcy5zeW5jQW5ub3RhdGlvbnMoKTtcbiAgfVxuXG4gIGJ0blpvb21JbkNsaWNrZWQoKSB7XG4gICAgdGhpcy53aW5kb3dTaXplSW5TZWMgPSBNYXRoLm1heCgwLCB0aGlzLndpbmRvd1NpemVJblNlYyAtIDAuNSk7XG4gICAgY29uc29sZS5sb2coJ3pvb21JbicsIHRoaXMud2luZG93U2l6ZUluU2VjKTtcbiAgfVxuXG4gIGJ0blpvb21PdXRDbGlja2VkKCkge1xuICAgIHRoaXMud2luZG93U2l6ZUluU2VjICs9IDAuNTtcbiAgICBjb25zb2xlLmxvZygnem9vbU91dCcsIHRoaXMud2luZG93U2l6ZUluU2VjKTtcbiAgfVxuXG4gIHRvZ2dsZVRhZ3NMaXN0KCkge1xuICAgIHRoaXMudGFnc0xpc3QuY2xhc3NMaXN0LnRvZ2dsZSgnc2hvdycpO1xuICB9XG5cbiAgc3luY0Fubm90YXRpb25zKCkge1xuICAgIHRoaXMubW9kZWwuc2V0KCdhbm5vdGF0aW9ucycsIFtdKTtcbiAgICB0aGlzLm1vZGVsLnNldCgnYW5ub3RhdGlvbnMnLCBbLi4udGhpcy5hbm5vdGF0aW9uc10pO1xuICAgIHRoaXMubW9kZWwuc2F2ZV9jaGFuZ2VzKCk7XG4gIH1cblxuICBjaGVja0ZvckFublNlbGVjdGlvbihtb3VzZVg6IG51bWJlcikge1xuICAgIGNvbnN0IHN0YXJ0VGltZSA9IHRoaXMuY3VycmVudFRpbWUgLSB0aGlzLndpbmRvd1NpemVJblNlYyAvIDI7XG4gICAgY29uc3QgZW5kVGltZSA9IHRoaXMuY3VycmVudFRpbWUgKyB0aGlzLndpbmRvd1NpemVJblNlYyAvIDI7XG5cbiAgICBjb25zdCBkcmF3bkFubnMgPSB0aGlzLmdldEFubm90YXRpb25zVG9EcmF3KHN0YXJ0VGltZSwgZW5kVGltZSk7XG5cbiAgICB0aGlzLnNlbGVjdGVkQW5uSW5kZXggPSBudWxsO1xuICAgIGZvciAobGV0IGkgPSAwOyBpIDwgZHJhd25Bbm5zLmxlbmd0aDsgaSsrKSB7XG4gICAgICBjb25zdCBhbm4gPSBkcmF3bkFubnNbaV07XG4gICAgICBpZiAoYW5uLnN0YXJ0ID4gbW91c2VYIHx8IGFubi5zdGFydCArIGFubi53aWR0aCA8IG1vdXNlWCkgY29udGludWU7XG4gICAgICB0aGlzLnNlbGVjdGVkQW5uSW5kZXggPSBhbm4uaW5kZXg7XG4gICAgICByZXR1cm4gdHJ1ZTtcbiAgICB9XG5cbiAgICByZXR1cm4gZmFsc2U7XG4gIH1cblxuICBjaGVja0ZvckhhbmRsZVNlbGVjdGlvbihtb3VzZVg6IG51bWJlcikge1xuICAgIGNvbnN0IHN0YXJ0VGltZSA9IHRoaXMuY3VycmVudFRpbWUgLSB0aGlzLndpbmRvd1NpemVJblNlYyAvIDI7XG4gICAgY29uc3QgZW5kVGltZSA9IHRoaXMuY3VycmVudFRpbWUgKyB0aGlzLndpbmRvd1NpemVJblNlYyAvIDI7XG5cbiAgICBjb25zdCBkcmF3bkFubnMgPSB0aGlzLmdldEFubm90YXRpb25zVG9EcmF3KHN0YXJ0VGltZSwgZW5kVGltZSk7XG5cbiAgICB0aGlzLnNlbGVjdGVkUmVzaXppbmdIYW5kbGUgPSBudWxsO1xuICAgIHRoaXMuc2VsZWN0ZWRNb3ZlSGFuZGxlID0gbnVsbDtcbiAgICBmb3IgKGxldCBpID0gMDsgaSA8IGRyYXduQW5ucy5sZW5ndGg7IGkrKykge1xuICAgICAgY29uc3QgYW5uID0gZHJhd25Bbm5zW2ldO1xuXG4gICAgICAvLyBDaGVjayBmb3IgbGVmdCBoYW5kbGVcbiAgICAgIGlmIChNYXRoLmFicyhtb3VzZVggLSBhbm4uc3RhcnQpIDwgNikge1xuICAgICAgICB0aGlzLnNlbGVjdGVkUmVzaXppbmdIYW5kbGUgPSB7XG4gICAgICAgICAgYW5uSW5kZXg6IGFubi5pbmRleCxcbiAgICAgICAgICBzaWRlOiAnbGVmdCcsXG4gICAgICAgIH07XG4gICAgICAgIHJldHVybiB0cnVlO1xuICAgICAgfVxuXG4gICAgICAvLyBDaGVjayBmb3IgcmlnaHQgaGFuZGxlXG4gICAgICBpZiAoTWF0aC5hYnMobW91c2VYIC0gYW5uLnN0YXJ0IC0gYW5uLndpZHRoKSA8IDYpIHtcbiAgICAgICAgdGhpcy5zZWxlY3RlZFJlc2l6aW5nSGFuZGxlID0ge1xuICAgICAgICAgIGFubkluZGV4OiBhbm4uaW5kZXgsXG4gICAgICAgICAgc2lkZTogJ3JpZ2h0JyxcbiAgICAgICAgfTtcbiAgICAgICAgcmV0dXJuIHRydWU7XG4gICAgICB9XG5cbiAgICAgIC8vIE1vdmUgaGFuZGxlXG4gICAgICBpZiAobW91c2VYID4gYW5uLnN0YXJ0ICYmIG1vdXNlWCA8IGFubi5zdGFydCArIGFubi53aWR0aCkge1xuICAgICAgICB0aGlzLnNlbGVjdGVkTW92ZUhhbmRsZSA9IHtcbiAgICAgICAgICBhbm5JbmRleDogYW5uLmluZGV4LFxuICAgICAgICAgIGdyYWJYOiBtb3VzZVgsXG4gICAgICAgICAgYW5uU3RhcnQ6IHRoaXMuYW5ub3RhdGlvbnNbYW5uLmluZGV4XS5zdGFydCxcbiAgICAgICAgICBhbm5FbmQ6IHRoaXMuYW5ub3RhdGlvbnNbYW5uLmluZGV4XS5lbmQsXG4gICAgICAgIH07XG4gICAgICB9XG4gICAgfVxuXG4gICAgcmV0dXJuIGZhbHNlO1xuICB9XG5cbiAgYWRkTGVnZW5kKCkge1xuICAgIGNvbnN0IGxlZ2VuZCA9IHRoaXMuZWwucXVlcnlTZWxlY3RvcignI2xlZ2VuZCcpITtcblxuICAgIGZvciAoY29uc3QgY2hhbm5lbCBvZiB0aGlzLm1vZGVsLmdldCgnY2hhbm5lbF9uYW1lcycpKSB7XG4gICAgICBjb25zdCBjaGFubmVsSW5kZXggPSB0aGlzLm1vZGVsXG4gICAgICAgIC5nZXQoJ2NoYW5uZWxfbmFtZXMnKVxuICAgICAgICAuZmluZEluZGV4KGUgPT4gZSA9PSBjaGFubmVsKTtcbiAgICAgIGNvbnN0IGxhYmVsID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgnc3BhbicpO1xuICAgICAgbGFiZWwuaW5uZXJIVE1MID0gY2hhbm5lbDtcbiAgICAgIGxhYmVsLnN0eWxlLnNldFByb3BlcnR5KCctLWxpbmUtY29sb3InLCB0aGlzLmdldFBsb3RDb2xvcihjaGFubmVsSW5kZXgpKTtcbiAgICAgIGxlZ2VuZC5hcHBlbmQobGFiZWwpO1xuICAgIH1cbiAgfVxuXG4gIGFkZFRpdGxlKCkge1xuICAgIGNvbnN0IHRpdGxlID0gdGhpcy5lbC5xdWVyeVNlbGVjdG9yKCcjdGl0bGUnKSE7XG4gICAgdGl0bGUuaW5uZXJIVE1MID0gdGhpcy5tb2RlbC5nZXQoJ3RpdGxlJyk7XG4gIH1cblxuICBnZXRQbG90Q29sb3IoY2hhbm5lbEluZGV4OiBudW1iZXIpIHtcbiAgICBjb25zdCBjb2xvcnMgPSBbXG4gICAgICAnI0Y0NDMzNicsXG4gICAgICAnIzRDQUY1MCcsXG4gICAgICAnIzIxOTZGMycsXG4gICAgICAnI0ZGRUIzQicsXG4gICAgICAnIzc5NTU0OCcsXG4gICAgICAnIzY3M0FCNycsXG4gICAgXTtcblxuICAgIGNvbnN0IGluZGV4ID0gY2hhbm5lbEluZGV4ICUgY29sb3JzLmxlbmd0aDtcblxuICAgIHJldHVybiBjb2xvcnNbaW5kZXhdO1xuICB9XG5cbiAgZ2V0VGFnQ29sb3IodGFnSW5kZXg6IG51bWJlcikge1xuICAgIGNvbnN0IGNvbG9ycyA9IFtcbiAgICAgICcjRjQ0MzM2JyxcbiAgICAgICcjM0Y1MUI1JyxcbiAgICAgICcjMDBCQ0Q0JyxcbiAgICAgICcjOUMyN0IwJyxcbiAgICAgICcjRTkxRTYzJyxcbiAgICAgICcjQ0REQzM5JyxcbiAgICAgICcjNzk1NTQ4JyxcbiAgICAgICcjRkZFQjNCJyxcbiAgICAgICcjNjA3RDhCJyxcbiAgICAgICcjMjE5NkYzJyxcbiAgICBdO1xuXG4gICAgY29uc3QgaW5kZXggPSB0YWdJbmRleCAlIGNvbG9ycy5sZW5ndGg7XG5cbiAgICByZXR1cm4gY29sb3JzW2luZGV4XTtcbiAgfVxuXG4gIHN0ZXAodGltZXN0YW1wOiBET01IaWdoUmVzVGltZVN0YW1wKSB7XG4gICAgaWYgKCF0aGlzLmxhc3RBbmltYXRpb25GcmFtZVRpbWVzdGFtcCkge1xuICAgICAgY29uc3QgY2FudmFzSG9sZGVyID0gdGhpcy5lbC5xdWVyeVNlbGVjdG9yKCcjY2FudmFzLWhvbGRlcicpITtcbiAgICAgIHRoaXMuY2FudmFzLndpZHRoID0gY2FudmFzSG9sZGVyLmNsaWVudFdpZHRoO1xuICAgICAgdGhpcy5jYW52YXMuaGVpZ2h0ID0gY2FudmFzSG9sZGVyLmNsaWVudEhlaWdodDtcbiAgICAgIHRoaXMuY2FudmFzLnN0eWxlLndpZHRoID0gJzEwMCUnO1xuICAgICAgdGhpcy5jYW52YXMuc3R5bGUuaGVpZ2h0ID0gJzEwMCUnO1xuXG4gICAgICB0aGlzLmxhc3RBbmltYXRpb25GcmFtZVRpbWVzdGFtcCA9IHRpbWVzdGFtcDtcbiAgICB9XG5cbiAgICBjb25zdCBkZWx0YSA9IHRpbWVzdGFtcCAtIHRoaXMubGFzdEFuaW1hdGlvbkZyYW1lVGltZXN0YW1wO1xuICAgIHRoaXMubGFzdEFuaW1hdGlvbkZyYW1lVGltZXN0YW1wID0gdGltZXN0YW1wO1xuXG4gICAgaWYgKHRoaXMubW9kZWwuZ2V0KCdpc19ydW5uaW5nJykpIHtcbiAgICAgIGNvbnN0IGR1cmF0aW9uID0gdGhpcy50aW1lc1t0aGlzLnRpbWVzLmxlbmd0aCAtIDFdO1xuICAgICAgdGhpcy5jdXJyZW50VGltZSA9IE1hdGgubWluKHRoaXMuY3VycmVudFRpbWUgKyBkZWx0YSAvIDEwMDAsIGR1cmF0aW9uKTtcbiAgICB9XG5cbiAgICB0aGlzLmNsZWFyRnJhbWUoKTtcbiAgICB0aGlzLmRyYXcoKTtcblxuICAgIHRoaXMuYW5pbWF0aW9uRnJhbWVSZXF1ZXN0SWQgPSByZXF1ZXN0QW5pbWF0aW9uRnJhbWUodGhpcy5zdGVwKTtcbiAgfVxuXG4gIGRyYXcoKSB7XG4gICAgY29uc3Qgc3RhcnRUaW1lID0gdGhpcy5jdXJyZW50VGltZSAtIHRoaXMud2luZG93U2l6ZUluU2VjIC8gMjtcbiAgICBjb25zdCBlbmRUaW1lID0gdGhpcy5jdXJyZW50VGltZSArIHRoaXMud2luZG93U2l6ZUluU2VjIC8gMjtcblxuICAgIGNvbnN0IHN0YXJ0SW5kZXggPSB0aGlzLnRpbWVzLmZpbmRJbmRleChlID0+IGUgPj0gc3RhcnRUaW1lKTtcbiAgICBjb25zdCBlbmRJbmRleFBsdXMxID0gdGhpcy50aW1lcy5maW5kSW5kZXgoZSA9PiBlID4gZW5kVGltZSk7XG5cbiAgICBjb25zdCBlbmRJbmRleCA9XG4gICAgICBlbmRJbmRleFBsdXMxICE9IC0xXG4gICAgICAgID8gTWF0aC5tYXgoZW5kSW5kZXhQbHVzMSAtIDEsIDApXG4gICAgICAgIDogdGhpcy50aW1lcy5sZW5ndGggLSAxO1xuXG4gICAgY29uc3QgZmlyc3RQb2ludFRpbWVEZWx0YSA9IHRoaXMudGltZXNbc3RhcnRJbmRleF0gLSB0aGlzLmN1cnJlbnRUaW1lO1xuICAgIGNvbnN0IGxhc3RQb2ludFRpbWVEZWx0YSA9IHRoaXMudGltZXNbZW5kSW5kZXhdIC0gdGhpcy5jdXJyZW50VGltZTtcbiAgICBjb25zdCBsZWZ0T2Zmc2V0UGVyY2VudGFnZSA9IE1hdGgubWF4KFxuICAgICAgZmlyc3RQb2ludFRpbWVEZWx0YSAvIHRoaXMud2luZG93U2l6ZUluU2VjICsgMC41LFxuICAgICAgMFxuICAgICk7XG4gICAgY29uc3QgcmlnaHRPZmZzZXRQZXJjZW50YWdlID1cbiAgICAgIGxhc3RQb2ludFRpbWVEZWx0YSAvIHRoaXMud2luZG93U2l6ZUluU2VjICsgMC41O1xuXG4gICAgdGhpcy5kcmF3QW5ub3RhdGlvbnMoc3RhcnRUaW1lLCBlbmRUaW1lKTtcblxuICAgIGZvciAobGV0IGMgPSAwOyBjIDwgdGhpcy5udW1DaGFubmVsczsgYysrKSB7XG4gICAgICB0aGlzLmRyYXdQbG90KFxuICAgICAgICBjLFxuICAgICAgICBzdGFydEluZGV4LFxuICAgICAgICBlbmRJbmRleCxcbiAgICAgICAgbGVmdE9mZnNldFBlcmNlbnRhZ2UsXG4gICAgICAgIHJpZ2h0T2Zmc2V0UGVyY2VudGFnZVxuICAgICAgKTtcbiAgICB9XG4gIH1cblxuICBnZXRSYW5nZShzdGFydEluZGV4OiBudW1iZXIsIGVuZEluZGV4OiBudW1iZXIpIHtcbiAgICBsZXQgbWluID0gdGhpcy55UmFuZ2UubWluO1xuICAgIGxldCBtYXggPSB0aGlzLnlSYW5nZS5tYXg7XG5cbiAgICBpZiAobWluICE9IG51bGwgJiYgbWF4ICE9IG51bGwpIHJldHVybiB7IG1pbiwgbWF4IH07XG5cbiAgICBjb25zdCBtaW5zID0gW107XG4gICAgY29uc3QgbWF4cyA9IFtdO1xuXG4gICAgZm9yIChsZXQgYyA9IDA7IGMgPCB0aGlzLm51bUNoYW5uZWxzOyBjKyspIHtcbiAgICAgIGlmIChtaW4gPT0gbnVsbCkge1xuICAgICAgICBtaW5zLnB1c2goTWF0aC5taW4oLi4udGhpcy52YWx1ZXNbY10uc2xpY2Uoc3RhcnRJbmRleCwgZW5kSW5kZXggKyAxKSkpO1xuICAgICAgfVxuICAgICAgaWYgKG1heCA9PSBudWxsKSB7XG4gICAgICAgIG1heHMucHVzaChNYXRoLm1heCguLi50aGlzLnZhbHVlc1tjXS5zbGljZShzdGFydEluZGV4LCBlbmRJbmRleCArIDEpKSk7XG4gICAgICB9XG4gICAgfVxuXG4gICAgcmV0dXJuIHtcbiAgICAgIG1pbjogbWluID8gbWluIDogTWF0aC5taW4oLi4ubWlucyksXG4gICAgICBtYXg6IG1heCA/IG1heCA6IE1hdGgubWF4KC4uLm1heHMpLFxuICAgIH07XG4gIH1cblxuICBkcmF3UGxvdChcbiAgICBjaGFubmVsSW5kZXg6IG51bWJlcixcbiAgICBzdGFydEluZGV4OiBudW1iZXIsXG4gICAgZW5kSW5kZXg6IG51bWJlcixcbiAgICBsZWZ0T2Zmc2V0UGVyY2VudGFnZTogbnVtYmVyLFxuICAgIHJpZ2h0T2Zmc2V0UGVyY2VudGFnZTogbnVtYmVyXG4gICkge1xuICAgIGlmIChpc05hTihzdGFydEluZGV4KSB8fCBpc05hTihlbmRJbmRleCkpIHJldHVybjtcblxuICAgIGNvbnN0IGN0eCA9IHRoaXMuY2FudmFzLmdldENvbnRleHQoJzJkJyk7XG4gICAgY29uc3Qgd2lkdGggPSB0aGlzLmNhbnZhcy53aWR0aDtcbiAgICBjb25zdCBoZWlnaHQgPSB0aGlzLmNhbnZhcy5oZWlnaHQ7XG5cbiAgICBpZiAoIWN0eCkge1xuICAgICAgY29uc29sZS5lcnJvcignRmFpbGVkIHRvIGdldCAyRCBjb250ZXh0Jyk7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgY3R4LnN0cm9rZVN0eWxlID0gdGhpcy5nZXRQbG90Q29sb3IoY2hhbm5lbEluZGV4KTtcbiAgICBjdHgubGluZVdpZHRoID0gMjtcblxuICAgIGN0eC5iZWdpblBhdGgoKTtcblxuICAgIGNvbnN0IGluZGV4UmFuZ2UgPSBlbmRJbmRleCAtIHN0YXJ0SW5kZXg7XG4gICAgY29uc3QgZnVsbFdpZHRoUmFuZ2UgPSB3aWR0aDtcbiAgICBjb25zdCBzdGFydFggPSBsZWZ0T2Zmc2V0UGVyY2VudGFnZSAqIGZ1bGxXaWR0aFJhbmdlO1xuICAgIGNvbnN0IGVuZFggPSByaWdodE9mZnNldFBlcmNlbnRhZ2UgKiBmdWxsV2lkdGhSYW5nZTtcbiAgICBjb25zdCB3aWR0aFJhbmdlID0gZW5kWCAtIHN0YXJ0WDtcbiAgICBjb25zdCBoZWlnaHRSYW5nZSA9IGhlaWdodDtcbiAgICBjb25zdCB7IG1pbiwgbWF4IH0gPSB0aGlzLmdldFJhbmdlKHN0YXJ0SW5kZXgsIGVuZEluZGV4KTtcbiAgICBjb25zdCB5UmFuZ2UgPSBtYXggLSBtaW47XG5cbiAgICBjb25zdCB2YWx1ZXMgPSB0aGlzLnZhbHVlc1tjaGFubmVsSW5kZXhdO1xuXG4gICAgY3R4Lm1vdmVUbyhcbiAgICAgIHN0YXJ0WCxcbiAgICAgIGhlaWdodCAtIChoZWlnaHRSYW5nZSAqICh2YWx1ZXNbc3RhcnRJbmRleF0gLSBtaW4pKSAvIHlSYW5nZVxuICAgICk7XG5cbiAgICBjb25zdCBtYXhfcG9pbnRzX3RvX2Rpc3BsYXkgPSB3aWR0aDtcbiAgICBjb25zdCBkaSA9XG4gICAgICBpbmRleFJhbmdlID4gbWF4X3BvaW50c190b19kaXNwbGF5XG4gICAgICAgID8gTWF0aC5mbG9vcihpbmRleFJhbmdlIC8gbWF4X3BvaW50c190b19kaXNwbGF5KVxuICAgICAgICA6IDE7XG5cbiAgICBmb3IgKFxuICAgICAgbGV0IGkgPSBNYXRoLm1heCgwLCBzdGFydEluZGV4IC0gZGkpO1xuICAgICAgaSA8IE1hdGgubWluKHZhbHVlcy5sZW5ndGgsIGVuZEluZGV4ICsgMiAqIGRpKTtcbiAgICAgIGkgKz0gZGlcbiAgICApIHtcbiAgICAgIGNvbnN0IHggPSAoKGkgLSBzdGFydEluZGV4KSAvIGluZGV4UmFuZ2UpICogd2lkdGhSYW5nZSArIHN0YXJ0WDtcbiAgICAgIGNvbnN0IHkgPSBoZWlnaHQgLSAoaGVpZ2h0UmFuZ2UgKiAodmFsdWVzW2ldIC0gbWluKSkgLyB5UmFuZ2U7XG4gICAgICBjdHgubGluZVRvKHgsIHkpO1xuICAgIH1cblxuICAgIGN0eC5zdHJva2UoKTtcbiAgfVxuXG4gIGdldEFubm90YXRpb25zVG9EcmF3KHN0YXJ0VGltZTogbnVtYmVyLCBlbmRUaW1lOiBudW1iZXIpIHtcbiAgICBsZXQgYW5ub3RhdGlvbnNUb0RyYXcgPSBbXTtcblxuICAgIGNvbnN0IHdpZHRoID0gdGhpcy5jYW52YXMud2lkdGg7XG5cbiAgICBjb25zdCBsZWZ0T2Zmc2V0UGVyY2VudGFnZSA9IDA7XG4gICAgY29uc3QgcmlnaHRPZmZzZXRQZXJjZW50YWdlID0gMTtcblxuICAgIGNvbnN0IGZ1bGxXaWR0aFJhbmdlID0gd2lkdGg7XG4gICAgY29uc3Qgc3RhcnRYID0gZnVsbFdpZHRoUmFuZ2UgKiBsZWZ0T2Zmc2V0UGVyY2VudGFnZTtcbiAgICBjb25zdCBlbmRYID0gZnVsbFdpZHRoUmFuZ2UgKiByaWdodE9mZnNldFBlcmNlbnRhZ2U7XG4gICAgY29uc3Qgd2lkdGhSYW5nZSA9IGVuZFggLSBzdGFydFg7XG4gICAgY29uc3QgdGltZVJhbmdlID0gZW5kVGltZSAtIHN0YXJ0VGltZTtcblxuICAgIGZvciAobGV0IGkgPSAwOyBpIDwgdGhpcy5hbm5vdGF0aW9ucy5sZW5ndGg7IGkrKykge1xuICAgICAgY29uc3QgYW5uID0gdGhpcy5hbm5vdGF0aW9uc1tpXTtcbiAgICAgIGlmIChcbiAgICAgICAgKGFubi5zdGFydCA+PSBzdGFydFRpbWUgJiYgYW5uLnN0YXJ0IDw9IGVuZFRpbWUpIHx8XG4gICAgICAgIChhbm4uZW5kID49IHN0YXJ0VGltZSAmJiBhbm4uZW5kIDw9IGVuZFRpbWUpIHx8XG4gICAgICAgIChhbm4uc3RhcnQgPD0gc3RhcnRUaW1lICYmIGFubi5lbmQgPj0gZW5kVGltZSlcbiAgICAgICkge1xuICAgICAgICBjb25zdCBzdGFydCA9XG4gICAgICAgICAgKHdpZHRoUmFuZ2UgKiAoTWF0aC5tYXgoYW5uWydzdGFydCddLCBzdGFydFRpbWUpIC0gc3RhcnRUaW1lKSkgL1xuICAgICAgICAgIHRpbWVSYW5nZTtcbiAgICAgICAgY29uc3QgZW5kID1cbiAgICAgICAgICAod2lkdGhSYW5nZSAqIChNYXRoLm1pbihhbm5bJ2VuZCddLCBlbmRUaW1lKSAtIHN0YXJ0VGltZSkpIC9cbiAgICAgICAgICB0aW1lUmFuZ2U7XG5cbiAgICAgICAgYW5ub3RhdGlvbnNUb0RyYXcucHVzaCh7XG4gICAgICAgICAgc3RhcnQ6IHN0YXJ0WCArIHN0YXJ0LFxuICAgICAgICAgIHdpZHRoOiBlbmQgLSBzdGFydCxcbiAgICAgICAgICB0YWdJbmRleGVzOiBhbm4udGFncy5tYXAodCA9PiB0aGlzLnRhZ3MuaW5kZXhPZih0KSksXG4gICAgICAgICAgaW5kZXg6IGksXG4gICAgICAgIH0pO1xuICAgICAgfVxuICAgIH1cblxuICAgIHJldHVybiBhbm5vdGF0aW9uc1RvRHJhdztcbiAgfVxuXG4gIGRyYXdBbm5vdGF0aW9ucyhzdGFydFRpbWU6IG51bWJlciwgZW5kVGltZTogbnVtYmVyKSB7XG4gICAgY29uc3QgY3R4ID0gdGhpcy5jYW52YXMuZ2V0Q29udGV4dCgnMmQnKTtcblxuICAgIGlmICghY3R4KSB7XG4gICAgICBjb25zb2xlLmVycm9yKCdGYWlsZWQgdG8gZ2V0IDJEIGNvbnRleHQnKTtcbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICBjb25zdCBoZWlnaHQgPSB0aGlzLmNhbnZhcy5oZWlnaHQ7XG4gICAgY29uc3QgaW5kaWNhdG9yUGFkZGluZyA9IDI7XG4gICAgY29uc3QgaW5kaWNhdG9ySGVpZ2h0ID0gNTtcblxuICAgIGNvbnN0IGFubm90YXRpb25zVG9EcmF3ID0gdGhpcy5nZXRBbm5vdGF0aW9uc1RvRHJhdyhzdGFydFRpbWUsIGVuZFRpbWUpO1xuXG4gICAgZm9yIChsZXQgaSA9IDA7IGkgPCBhbm5vdGF0aW9uc1RvRHJhdy5sZW5ndGg7IGkrKykge1xuICAgICAgY29uc3QgYW5uID0gYW5ub3RhdGlvbnNUb0RyYXdbaV07XG5cbiAgICAgIGN0eC5maWxsU3R5bGUgPSBgIzc4OTA5QyR7YW5uLmluZGV4ID09IHRoaXMuc2VsZWN0ZWRBbm5JbmRleCA/ICc0NCcgOiAnMjInfWA7XG4gICAgICBjdHguZmlsbFJlY3QoYW5uLnN0YXJ0LCAwLCBhbm4ud2lkdGgsIGhlaWdodCk7XG5cbiAgICAgIGZvciAobGV0IGkgPSAwOyBpIDwgYW5uLnRhZ0luZGV4ZXMubGVuZ3RoOyBpKyspIHtcbiAgICAgICAgY3R4LmZpbGxTdHlsZSA9IHRoaXMuZ2V0VGFnQ29sb3IoYW5uLnRhZ0luZGV4ZXNbaV0pO1xuICAgICAgICBjdHguZmlsbFJlY3QoXG4gICAgICAgICAgYW5uLnN0YXJ0ICsgaW5kaWNhdG9yUGFkZGluZyxcbiAgICAgICAgICBpbmRpY2F0b3JQYWRkaW5nICsgaSAqIGluZGljYXRvckhlaWdodCxcbiAgICAgICAgICBhbm4ud2lkdGggLSAyICogaW5kaWNhdG9yUGFkZGluZyxcbiAgICAgICAgICBpbmRpY2F0b3JIZWlnaHQgLSBpbmRpY2F0b3JQYWRkaW5nXG4gICAgICAgICk7XG4gICAgICB9XG5cbiAgICAgIGlmICh0aGlzLnNlbGVjdGVkQW5uSW5kZXggPT0gYW5uLmluZGV4KSB7XG4gICAgICAgIGN0eC5saW5lQ2FwID0gJ3JvdW5kJztcbiAgICAgICAgY3R4LnN0cm9rZVN0eWxlID0gJyM3ODkwOUMnO1xuICAgICAgICBjdHgubGluZVdpZHRoID0gNDtcblxuICAgICAgICAvLyBMZWZ0IGhhbmRsZVxuICAgICAgICBjdHguYmVnaW5QYXRoKCk7XG4gICAgICAgIGN0eC5tb3ZlVG8oYW5uLnN0YXJ0IC0gNCwgaGVpZ2h0IC8gMiAtIDEyKTtcbiAgICAgICAgY3R4LmxpbmVUbyhhbm4uc3RhcnQgLSA0LCBoZWlnaHQgLyAyICsgMTIpO1xuICAgICAgICBjdHguc3Ryb2tlKCk7XG5cbiAgICAgICAgY3R4LmJlZ2luUGF0aCgpO1xuICAgICAgICBjdHgubW92ZVRvKGFubi5zdGFydCArIDQsIGhlaWdodCAvIDIgLSAxMik7XG4gICAgICAgIGN0eC5saW5lVG8oYW5uLnN0YXJ0ICsgNCwgaGVpZ2h0IC8gMiArIDEyKTtcbiAgICAgICAgY3R4LnN0cm9rZSgpO1xuXG4gICAgICAgIC8vIFJpZ2h0IGhhbmRsZVxuICAgICAgICBjdHguYmVnaW5QYXRoKCk7XG4gICAgICAgIGN0eC5tb3ZlVG8oYW5uLnN0YXJ0ICsgYW5uLndpZHRoIC0gNCwgaGVpZ2h0IC8gMiAtIDEyKTtcbiAgICAgICAgY3R4LmxpbmVUbyhhbm4uc3RhcnQgKyBhbm4ud2lkdGggLSA0LCBoZWlnaHQgLyAyICsgMTIpO1xuICAgICAgICBjdHguc3Ryb2tlKCk7XG5cbiAgICAgICAgY3R4LmJlZ2luUGF0aCgpO1xuICAgICAgICBjdHgubW92ZVRvKGFubi5zdGFydCArIGFubi53aWR0aCArIDQsIGhlaWdodCAvIDIgLSAxMik7XG4gICAgICAgIGN0eC5saW5lVG8oYW5uLnN0YXJ0ICsgYW5uLndpZHRoICsgNCwgaGVpZ2h0IC8gMiArIDEyKTtcbiAgICAgICAgY3R4LnN0cm9rZSgpO1xuICAgICAgfVxuICAgIH1cbiAgfVxuXG4gIGNsZWFyRnJhbWUoKSB7XG4gICAgY29uc3QgY3R4ID0gdGhpcy5jYW52YXMuZ2V0Q29udGV4dCgnMmQnKTtcbiAgICBjb25zdCB3aWR0aCA9IHRoaXMuY2FudmFzLndpZHRoO1xuICAgIGNvbnN0IGhlaWdodCA9IHRoaXMuY2FudmFzLmhlaWdodDtcblxuICAgIGlmICghY3R4KSB7XG4gICAgICBjb25zb2xlLmVycm9yKCdGYWlsZWQgdG8gZ2V0IDJEIGNvbnRleHQnKTtcbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICBjdHguY2xlYXJSZWN0KDAsIDAsIHdpZHRoLCBoZWlnaHQpO1xuXG4gICAgdGhpcy5kcmF3QXhpcyhjdHgsIHdpZHRoLCBoZWlnaHQpO1xuICAgIHRoaXMuZHJhd1hMYWJlbHMoY3R4LCB3aWR0aCwgaGVpZ2h0KTtcbiAgfVxuXG4gIGRyYXdBeGlzKGN0eDogQ2FudmFzUmVuZGVyaW5nQ29udGV4dDJELCB3aWR0aDogbnVtYmVyLCBoZWlnaHQ6IG51bWJlcikge1xuICAgIGN0eC5zdHJva2VTdHlsZSA9ICcjNjA3ZDhiJztcblxuICAgIGN0eC5iZWdpblBhdGgoKTtcbiAgICBjdHgubW92ZVRvKDAsIGhlaWdodCAvIDIpO1xuICAgIGN0eC5saW5lVG8od2lkdGgsIGhlaWdodCAvIDIpO1xuICAgIGN0eC5zdHJva2UoKTtcblxuICAgIC8vIGN0eC5iZWdpblBhdGgoKTtcbiAgICAvLyBjdHgubW92ZVRvKHdpZHRoIC8gMiwgMCk7XG4gICAgLy8gY3R4LmxpbmVUbyh3aWR0aCAvIDIsIGhlaWdodCk7XG4gICAgLy8gY3R4LnN0cm9rZSgpO1xuICB9XG5cbiAgZHJhd1hMYWJlbHMoY3R4OiBDYW52YXNSZW5kZXJpbmdDb250ZXh0MkQsIHdpZHRoOiBudW1iZXIsIGhlaWdodDogbnVtYmVyKSB7XG4gICAgY29uc3QgdGlja3NUb0RyYXcgPSA1O1xuICAgIGNvbnN0IHRpY2tzVG9EcmF3SGFsZiA9IE1hdGguZmxvb3IodGlja3NUb0RyYXcpO1xuXG4gICAgY29uc3QgbWlkZGxlVGlja1RpbWUgPVxuICAgICAgKHRoaXMud2luZG93U2l6ZUluU2VjIC8gdGlja3NUb0RyYXcpICpcbiAgICAgIE1hdGguZmxvb3IodGhpcy5jdXJyZW50VGltZSAvICh0aGlzLndpbmRvd1NpemVJblNlYyAvIHRpY2tzVG9EcmF3KSk7XG5cbiAgICBjdHguc3Ryb2tlU3R5bGUgPSAnI0IwQkVDNSc7XG4gICAgY3R4LmZpbGxTdHlsZSA9ICcjNjA3ZDhiJztcbiAgICBjdHguZm9udCA9ICcxMnB4IEFyaWFsJztcblxuICAgIGZvciAobGV0IGkgPSAtdGlja3NUb0RyYXdIYWxmOyBpIDw9IHRpY2tzVG9EcmF3SGFsZiArIDE7IGkgKz0gMSkge1xuICAgICAgY29uc3QgdGlja1RpbWUgPVxuICAgICAgICBpICogKHRoaXMud2luZG93U2l6ZUluU2VjIC8gdGlja3NUb0RyYXcpICsgbWlkZGxlVGlja1RpbWU7XG4gICAgICBjb25zdCB4ID0gKHdpZHRoICogKHRpY2tUaW1lIC0gdGhpcy5jdXJyZW50VGltZSkpIC8gdGhpcy53aW5kb3dTaXplSW5TZWM7XG5cbiAgICAgIGN0eC5iZWdpblBhdGgoKTtcbiAgICAgIGN0eC5tb3ZlVG8oeCwgMCk7XG4gICAgICBjdHgubGluZVRvKHgsIGhlaWdodCk7XG4gICAgICBjdHguc3Ryb2tlKCk7XG5cbiAgICAgIGN0eC5maWxsVGV4dChcbiAgICAgICAgKHRpY2tUaW1lIC0gdGhpcy53aW5kb3dTaXplSW5TZWMgLyAyKS50b0ZpeGVkKDIpLFxuICAgICAgICB4ICsgNCxcbiAgICAgICAgaGVpZ2h0IC0gNFxuICAgICAgKTtcbiAgICB9XG4gIH1cblxuICBzeW5jVGltZUNoYW5nZWQoKSB7XG4gICAgdGhpcy5jdXJyZW50VGltZSA9IHRoaXMubW9kZWwuZ2V0KCdzeW5jX3RpbWUnKTtcbiAgfVxuXG4gIGlzUnVubmluZ0NoYW5nZWQoKSB7fVxuXG4gIHJlbmRlcigpIHtcbiAgICB0aGlzLm1vZGVsLm9uKCdjaGFuZ2U6c3luY190aW1lJywgdGhpcy5zeW5jVGltZUNoYW5nZWQuYmluZCh0aGlzKSk7XG4gICAgdGhpcy5tb2RlbC5vbignY2hhbmdlOmlzX3J1bm5pbmcnLCB0aGlzLmlzUnVubmluZ0NoYW5nZWQuYmluZCh0aGlzKSk7XG5cbiAgICB0aGlzLnN0ZXAgPSB0aGlzLnN0ZXAuYmluZCh0aGlzKTtcbiAgICB0aGlzLmFuaW1hdGlvbkZyYW1lUmVxdWVzdElkID0gcmVxdWVzdEFuaW1hdGlvbkZyYW1lKHRoaXMuc3RlcCk7XG4gIH1cblxuICBkZXN0cm95KCkge1xuICAgIGNhbmNlbEFuaW1hdGlvbkZyYW1lKHRoaXMuYW5pbWF0aW9uRnJhbWVSZXF1ZXN0SWQhKTtcbiAgfVxufVxuXG5leHBvcnQgZGVmYXVsdCB7XG4gIHJlbmRlcihwcm9wczogUmVuZGVyUHJvcHM8VGltZXJzZXJpZXNXaWRnZXRNb2RlbD4pIHtcbiAgICBjb25zdCB3aWRnZXQgPSBuZXcgVGltZXNlcmllc1dpZGdldChwcm9wcyk7XG4gICAgd2lkZ2V0LnJlbmRlcigpO1xuICAgIHJldHVybiAoKSA9PiB3aWRnZXQuZGVzdHJveSgpO1xuICB9LFxufTtcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBQTs7O0FDbUNBLElBQU0sbUJBQU4sTUFBdUI7QUFBQSxFQXFDckIsWUFBWSxF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LEVBRUEsbUJBQW1CO0FBQUEsRUFBQztBQUFBLEVBRXBCLFNBQVM7QUFDUCxTQUFLLE1BQU0sR0FBRyxvQkFBb0IsS0FBSyxnQkFBZ0IsS0FBSyxJQUFJLENBQUM7QUFDakUsU0FBSyxNQUFNLEdBQUcscUJBQXFCLEtBQUssaUJBQWlCLEtBQUssSUFBSSxDQUFDO0FBRW5FLFNBQUssT0FBTyxLQUFLLEtBQUssS0FBSyxJQUFJO0FBQy9CLFNBQUssMEJBQTBCLHNCQUFzQixLQUFLLElBQUk7QUFBQSxFQUNoRTtBQUFBLEVBRUEsVUFBVTtBQUNSLHlCQUFxQixLQUFLLHVCQUF3QjtBQUFBLEVBQ3BEO0FBQ0Y7QUFFQSxJQUFPQyw2QkFBUTtBQUFBLEVBQ2IsT0FBTyxPQUE0QztBQUNqRCxVQUFNLFNBQVMsSUFBSSxpQkFBaUIsS0FBSztBQUN6QyxXQUFPLE9BQU87QUFDZCxXQUFPLE1BQU0sT0FBTyxRQUFRO0FBQUEsRUFDOUI7QUFDRjsiLAogICJuYW1lcyI6IFsiaSIsICJ0aW1lc2VyaWVzX3dpZGdldF9kZWZhdWx0Il0KfQo=
