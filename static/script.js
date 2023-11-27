function handleFormSubmission(event) {
    event.preventDefault();

    var youtubeId = $('#youtube_id').val();

    callProcessApi(youtubeId)
        .then(function (data) {
            // Call a function to handle the result and redirect
            handleProcessApiResult(data);
        })
        .catch(function (error) {
            // Handle errors if necessary
            console.error("Error:", error);
        });
}


function callProcessApi(youtubeId) {
    return new Promise(function (resolve, reject) {
        $.ajax({
            type: 'POST',
            url: '/processapi',
            data: { 'youtube_id': youtubeId },
            success: function (data) {
                resolve(data);
            },
            error: function (error) {
                reject(error);
            }
        });
    });
}


function handleProcessApiResult(data) {
    console.log("Processing finished. Redirecting to /results/" + data);
    window.location.href = '/results/' + data;
}
