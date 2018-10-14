// TODO: provide ui for choosing part of image to filter (define filter function based on chocie)
const video = document.querySelector("#video-player");
const canvas = document.querySelector("#booth-photo");
const ctx = canvas.getContext("2d");
const strip = document.querySelector(".strip");
const snap = document.querySelector(".snap");
const shutter = document.querySelector(".take-photo");
const buttons = document.querySelectorAll("a");
// const effectControls = document.querySelectorAll(".controls");
// const colorizeControls = document.querySelectorAll('input[name="colorize"]');
const backendUri = "https://128.61.105.52/";
const requestFiltersUri = backendUri + "convert_encoded";
const sendMessageUri = backendUri + "send_mms";
var currentFrame = '';
var applyMask = () => {
    console.error("Apply mask called before binding");
};

// Gets mask id of hovered element if in canvas
var hoveredId = 0;

// Received from backend
var activeFilter = "";
// Q: will we receive same resolution? will backend send us another copy of no filter image?

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

/*
const paintToCanvas = () => {
    const width = video.videoWidth;
    const height = video.videoHeight;
    canvas.width = width;
    canvas.height = height;

    return setInterval(() => {
        ctx.drawImage(video, 0, 0, width, height);
        let pixels = ctx.getImageData(0, 0, width, height);
        if (activeEffect === "colorize") {
            ctx.globalAlpha = 1;
            colorize(pixels);
        } else if (activeEffect === "spectrascope") {
            ctx.globalAlpha = 0.3;
            spectrascope(pixels);
        } else if (activeEffect === "chromakey") {
            ctx.globalAlpha = 1;
            chromakey(pixels);
        }
        ctx.putImageData(pixels, 0, 0);
    }, 16);
};
*/

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
            // mock
            var img = new Image();

            img.onload = function(){
                canvas.height = img.height;
                canvas.width = img.width;
            }

            img.src = "/assets/images/source.jpg";
            var image = document.getElementById('source');
            ctx.drawImage(image, 0, 0);
            // var filt1 = document.getElementById('filter1');

            console.log(data.length);
            console.log(data[0].length);
            const filters = [0, 1, 2];
            applyMask = applyMaskBase.bind(this, ctx.getImageData(), data, data);
            $('#filter-wrap').show();
            $('#take-wrap').hide();
            $.each(data, function (index, value) {
               console.log(value);
            });
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

    // Handle outlines
    $('#booth-photo').mouseover(() => {
        
        console.log("Entered");
    }).mouseleave(() => {
        console.log("left");
    })
});

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
        if (maskData[i] == 1) { // TODO: sub in mask flag for figure
            pixelIndex = 4 * i;
            pixels.data[pixelIndex + 0] = filterData[pixelIndex][0];
            pixels.data[pixelIndex + 1] = filterData[pixelIndex][1];
            pixels.data[pixelIndex + 2] = filterData[pixelIndex][2];
        }
    }
    ctx.putImageData(pixels, 0, 0);
};
// video.addEventListener("canplay", paintToCanvas);


// Track mouse and deal with outlines and updating hover piece
function getMousePos(canvas, evt) {
    var rect = canvas.getBoundingClientRect();
    return {
        x: (evt.clientX - rect.left) / (rect.right - rect.left) * canvas.width,
        y: (evt.clientY - rect.top) / (rect.bottom - rect.top) * canvas.height
    };
}

