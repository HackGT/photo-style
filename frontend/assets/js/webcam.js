// TODO: provide ui for choosing part of image to filter (define filter function based on chocie)
const video = document.querySelector("#video-player");
const canvas = document.querySelector("#booth-photo");
const ctx = canvas.getContext("2d");
const activeCanvas = document.querySelector("#active-layer");
const activeCtx = activeCanvas.getContext("2d");
const hoverCanvas = document.querySelector("#hover-layer");
const hoverCtx = hoverCanvas.getContext("2d");

const snap = document.querySelector(".snap");
const backendUri = "https://128.61.105.52/";
const requestFiltersUri = backendUri + "convert_encoded";
const sendMessageUri = backendUri + "send_mms";
var currentFrame = '';
var applyMask = () => console.error("Apply mask called before binding");
var applyActiveOutline = () => console.error("Apply active outline called before binding");
var applyHoverOutline = () => console.error("Apply hover outline called before binding");

// Mask id of people/background
var hoverId = -1; // - 1 is none
var activeId = -1;
var activeFilter = ""; // label of filter

const getVideo = () => {
    navigator.mediaDevices
        .getUserMedia({
            video: true,
            audio: false
        })
        .then(localMediaStream => {
            video.src = window.URL.createObjectURL(localMediaStream);
            video.play();
        })
        .catch(err => {
            console.error(`error`, err);
        });
};

const takePhoto = () => {
    filterData = '';
    currentFrame = '';
    $("#photo-take").attr("disabled", true);
    $('#countdown-wrap').show();
    $("#countdown").countdown360({
        radius: 60.5,
        seconds: 1,
        strokeWidth: 15,
        fillStyle: '#FFF',
        strokeStyle: '#000',
        fontSize: 50,
        fontColor: '#000',
        autostart: false,
        onComplete: function () {
            snap.currentTime = 0;
            snap.play();
            video.pause();
            // Alternatively, call '/capture' here (if we want countdown)
            // await response and move on to preview
            // assume we have image in next stage
            // if we can't get preview, just send to backend, no preview stage
            $('#countdown-wrap').hide();
            $('#take-check').show();
            $('#photo-take').hide();
            // link.setAttribute("download", "photo");
            // link.classList.add("photo");
            // link.innerHTML = `<img src="${data}" alt="photo" />`;
            // // strip.insertBefore(link, strip.firstChild);
        }
    }).start()
};

const retakePhoto = () => {
    $('#take-check').hide();
    // $('#photo-take').attr("disabled", false); // This just isn't working
    $('#photo-take').show();
    video.play();
}

$(document).ready(function () {

    $('#take-wrap').hide();
    $('#filter-wrap').hide();
    
    $('#start-photo').click(function (e) {
        e.preventDefault();
        getVideo();
        $('#start-wrap').hide();
        $('#take-wrap').show();
        $('#take-check').hide();
    });

    $('#take-photo').click(function (e) {
        e.preventDefault();
        takePhoto();
        // Alternatively, call DSLR /capture api here
    });

    $('#retake-photo').click(retakePhoto);

    $('#confirm-photo').click(function (e) {
        e.preventDefault();
    
        // canvas.width = video.videoWidth; // BUG: why is this widening?
        // canvas.height = video.videoHeight;
        // create photo
        // ctx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
        
        // Mocked
        currentFrame = canvas.toDataURL();
        currentFilter = "";
        $('#filter-wrap').show();
        $('#take-wrap').hide();
        // connect to backend
        $.getJSON("/assets/images/mask1.json", function (data) {
            const trackMouseCanvas = trackMouseCanvasBase.bind(this, data);
            const srcData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const flatMask = flatten(data); 
            const flatFilters = [];
            applyActiveOutline = applyActiveOutlineBase.bind(this, flatMask); // right now active and hover the same...
            applyHoverOutline = applyHoverOutlineBase.bind(this, flatMask);
            applyMask = applyMaskBase.bind(this, srcData, flatMask, flatFilters);
            // mock
            var img = new Image();

            img.onload = function(){
                canvas.width = img.width;
                canvas.height = img.height;
                hoverCanvas.width = img.width;
                hoverCanvas.height = img.height;
                activeCanvas.width = img.width;
                activeCanvas.height = img.height;
                ctx.drawImage(img, 0, 0);
            }

            img.src = "/assets/images/source.jpg";
            var image = document.getElementById('source');
            // var filt1 = document.getElementById('filter1');
            $("#booth-photo").mousemove( event => {
                mouseDict = getMousePos(event);
                trackMouseCanvas(mouseDict);
            });
            $('#booth-photo').click( event => {
                if (activeId != hoverId) {
                    activeId = hoverId;
                    applyActiveOutline();
                } else {
                    activeId = -1;
                    activeCtx.clearRect(0, 0, activeCanvas.width, activeCanvas.height);
                }
            });

            const filters = [0, 1, 2];
            // So much is broken here
            $('#filter-wrap').show();
            $('#take-wrap').hide();
        });
        
        
        // $.post(requestFiltersUri, JSON.stringify({
        //     image_url: canvas.toDataURL()
        // }), function (data, status) {
        //     console.log(data, status)
        //     if (status == "success") {
        //         iziToast.info({
        //             title: 'FYI',
        //             message: 'Photo processed!'
        //         });
        //         applyMask = applyMaskBase.bind(this, canvas.getImageData(), data.mask, data.filters);
        //         $('#filter-wrap').show();
        //         $('#take-wrap').hide();
        //     } else {
        //         iziToast.error({
        //             title: 'Error',
        //             message: 'Something went wrong'
        //         });
        //     }
        // }).fail(function () {
        //     iziToast.error({
        //         title: 'Error',
        //         message: 'Something went wrong'
        //     });
        // });
    });

    // Filters
    $(".filter-option").click(e => {
        e.preventDefault();
        // CSS handling
        const filter = e.target.dataset.filter;
        if (filter === activeFilter) {
            activeFilter = null;
            e.target.classList.remove('active');
            applyMask();
        } else {
            // disable active filter
            if (!!activeFilter) {
                const activeNode = document.querySelector(
                    `[data-filter=${activeFilter}]`
                );
                activeNode ? activeNode.classList.remove('active') : null;
            }
            activeFilter = filter;
            e.target.classList.add('active');
            applyMask(filter);
        }
    });

    // Send

    $('#prompt-send').click(function (e) {
        $('#send-modal').modal();
    });
    

    $('#send-confirm').click(function (e) {
        const url = canvas.toDataURL(); // TODO: make sure this is right
        $.post(sendMessageUri, JSON.stringify({
            phone: $('#phone').val(),
            url: url
        }), function (data, status) {
            console.log(data, status)
            if (status == 'success') {
                iziToast.success({
                    title: 'FYI',
                    message: 'Photo messaged!'
                });
                window.location.reload();
            } else {
                iziToast.error({
                    title: 'Error',
                    message: 'Something went wrong',
                    style: $('input[name=filter]:checked').val()
                });
            }
        });
    });

    $('.restart-button').click(() => {
        window.location.reload();
    });

    $('#booth-photo').mouseleave(() => {
        hoverId = -1;
        hoverCtx.clearRect(0, 0, hoverCanvas.width, hoverCanvas.height);
    })
});

const applyActiveOutlineBase = (maskData) => {
    if (!maskData) {
        console.error("Illegal call of applyActiveOutline");
        return;
    }

    const pixels = activeCtx.getImageData(0, 0, activeCanvas.width, activeCanvas.height);
    activeCtx.clearRect(0, 0, activeCanvas.width, activeCanvas.height);
    for (let i = 0; i < pixels.data.length / 4; i += 1) {
        pixelIndex = 4 * i;
        if (maskData[i] == activeId) {
            // TODO: better colors
            pixels.data[pixelIndex + 0] = 0;
            pixels.data[pixelIndex + 1] = 0;
            pixels.data[pixelIndex + 2] = 255;
            pixels.data[pixelIndex + 3] = 255;
        }
    }
    activeCtx.putImageData(pixels, 0, 0);
}

const applyHoverOutlineBase = (maskData) => {
    if (!maskData) {
        console.error("Illegal call of applyHoverOutline");
        return;
    }

    const pixels = hoverCtx.getImageData(0, 0, hoverCanvas.width, hoverCanvas.height);
    hoverCtx.clearRect(0, 0, hoverCanvas.width, hoverCanvas.height);
    for (let i = 0; i < pixels.data.length / 4; i += 1) {
        pixelIndex = 4 * i;
        if (maskData[i] == hoverId) {
            // TODO: get some better colors in here dear god
            pixels.data[pixelIndex + 0] = 255;
            pixels.data[pixelIndex + 1] = 0;
            pixels.data[pixelIndex + 2] = 0;
            pixels.data[pixelIndex + 3] = 255;
        } else {
            pixels.data[pixelIndex + 3] = 0;
        }
    }
    hoverCtx.putImageData(pixels, 0, 0);
}

// Request data flattened
const applyMaskBase = (baseData, maskData, filterData, filter) => {
    if (!baseData || !maskData || !filterData) { // TODO: verify shape of data too
        console.error("Illegal call of applyMask");
        return;
    }

    const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height);
     if (!filter) {
        ctx.putImageData(baseData, 0, 0);
        return;
    }

    for (let i = 0; i < pixels.data.length / 4; i += 1) {
        // For each pixel
        // If outlines, apply set colors
        pixelIndex = 4 * i;
        if (maskData[i] == activeId) { // TODO: sub in actual filters
            pixelIndex = 4 * i;
            pixels.data[pixelIndex + 0] = 0;
            pixels.data[pixelIndex + 1] = 0;
            pixels.data[pixelIndex + 2] = 0;
            /*
            pixels.data[pixelIndex + 0] = filterData[pixelIndex][0];
            pixels.data[pixelIndex + 1] = filterData[pixelIndex][1];
            pixels.data[pixelIndex + 2] = filterData[pixelIndex][2];
            */
        }
    }
    ctx.putImageData(pixels, 0, 0);
};
// video.addEventListener("canplay", paintToCanvas);


/* Track mouse and deal with outlines and updating hover piece */
// Get mouse position in canvas, rounded
function getMousePos(evt) {
    var rect = canvas.getBoundingClientRect();
    return {
        x: Math.round((evt.clientX - rect.left) / (rect.right - rect.left) * canvas.width),
        y: Math.round((evt.clientY - rect.top) / (rect.bottom - rect.top) * canvas.height)
    };
}

// Sets hovered ID/tracks outline
const trackMouseCanvasBase = (maskData, mouseDict) => {
    if (!maskData) return;
    shouldUpdate = hoverId != maskData[mouseDict.y][mouseDict.x];
    hoverId = maskData[mouseDict.y][mouseDict.x];
    if (shouldUpdate)
        applyHoverOutline();
}

const flatten = function(arr, result = []) {
    for (let i = 0, length = arr.length; i < length; i++) {
        const value = arr[i];
        if (Array.isArray(value)) {
        flatten(value, result);
        } else {
        result.push(value);
        }
    }
    return result;
};