/// <reference path="../App.js" />

(function () {
    "use strict";

    // The initialize function must be run each time a new page is loaded
    Office.initialize = function (reason) {
        $(document).ready(function () {
            app.initialize();
            var picUrl;

            // If getSelectedDataAsync method is supported by the host application,
            // reads data from current document selection and displays a preview of the picture
            if (Office.context.document.getSelectedDataAsync) {
                $('#searhPictures').click(function () {
                    Office.context.document.getSelectedDataAsync(Office.CoercionType.Text,
                        function (result) {
                            if (result.status === Office.AsyncResultStatus.Succeeded) {
                                picUrl = result.value.trim();
                                if (validatePic(picUrl)) {
                                    preViewPic(picUrl);
                                }
                            } else {
                                app.showNotification('Error:', result.error.message);
                            }
                        }
                    );
                });
            }

            // If setSelectedDataAsync method is supported by the host application,
            // insertImageLink is hooked up to call the method
            if (Office.context.document.setSelectedDataAsync) {
                $('#insertImageLink').click(function () {
                    var imgHtml = "<img " + "src='" + picUrl + "' img/>";
                    setHTMLImage(imgHtml);
                });
            }
        });
    };

    // invalidate Picture Url
    function validatePic(picUrl) {
        if (picUrl.length == 0) {
            app.showNotification("Please select a text from the document to search awesome pictures.");
            return false;
        }

        var picextension = picUrl.substring(picUrl.lastIndexOf("."), picUrl.length);
        picextension = picextension.toLowerCase();
        if ((picextension != ".jpg") && (picextension != ".gif") && (picextension != ".jpeg") && (picextension != ".png") && (picextension != ".bmp")) {
            app.showNotification("Image type must be one of gif,jpeg,jpg,png");

            // Clear Picture Url
            picUrl = "";
            document.selection.clear();
            return false;
        }

        return true;
    }

    // Preview Picture to make sure that url is valid
    function preViewPic(picUrl) {
        $('#insertImageLinkThumbnail').prop("src", picUrl);
        $('#insertImageLink').prop("src", picUrl);
    }

    // Insert image 
    function setHTMLImage(imgHTML) {
        Office.context.document.setSelectedDataAsync(
            imgHTML,
            { coercionType: "html" },
            function (asyncResult) {
                if (asyncResult.status == "failed") {
                    writeError('Error: ' + asyncResult.error.message);
                }
            });
    }
})();