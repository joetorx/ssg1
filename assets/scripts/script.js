// MIT License

// Copyright (c) 2026 Joel Torres

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.


// Checks the current location in the nav and assigns 
// a class for coloring the nav item in the header


const current_url = new URL(window.location.href);
const navi = document.getElementById("navi");
const home_regex = new RegExp("/", "g");

let path_pos = 0;
if (navi.className === "nav-root") {
    path_pos = 1;
}
else if (navi.className === "nav-folder") {
    path_pos = 2;
}

if (path_pos !== 0) {
    const path_name = current_url.pathname;
    const freq_match = path_name.match(home_regex);
    const path_count = freq_match ? freq_match.length : 0;

    let nav_id;
    if (path_name === "/") {
        nav_id = "home";
    } else if (navi.className === "nav-folder" && path_count === 2) {
        nav_id = "home";
    }
    else {
        nav_id = path_name.split("/")[path_pos];
    }

    const nav_elem = document.getElementById(nav_id);
    nav_elem.className = "selected";
}
