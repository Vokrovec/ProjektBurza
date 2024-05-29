var slider_min = document.getElementById("minutes");
var slider_per = document.getElementById("percent")
var output_min = document.getElementById("sliderValueMin");
var output_per = document.getElementById("sliderValuePer");
output_min.innerHTML = slider_min.value; // Display the default slider value
output_per.innerHTML = slider_per.value
// Update the current slider value (each time you drag the slider handle)
slider_min.oninput = function() {
  output_min.innerHTML = this.value;
}
slider_per.oninput = function() {
  output_per.innerHTML = this.value;
} 