console.log("NestFind loaded successfully.");


/* =========================================================
   NESTFIND - PROPERTY IMAGE UPLOAD VALIDATION
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const propertyImages = document.getElementById("propertyImages");
    const imagePreviewContainer = document.getElementById("imagePreviewContainer");
    const imageCount = document.getElementById("imageCount");

    if (!propertyImages) {
        return;
    }

    const maxImages = 5;
    const maxSize = 5 * 1024 * 1024; // 5 MB

    const allowedTypes = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    ];


    /* =====================================================
       IMAGE SELECTION
       ===================================================== */

    propertyImages.addEventListener("change", function () {

        imagePreviewContainer.innerHTML = "";
        imageCount.style.display = "none";

        const files = Array.from(this.files);

        /* Maximum 5 images */

        if (files.length > maxImages) {

            alert("You can upload a maximum of 5 images.");

            this.value = "";

            return;
        }


        const validFiles = [];


        /* =================================================
           VALIDATE EACH IMAGE
           ================================================= */

        files.forEach(function (file) {

            /* Check file type */

            if (!allowedTypes.includes(file.type)) {

                alert(
                    file.name +
                    " is not a valid image format.\n\n" +
                    "Allowed formats: JPG, JPEG, PNG, WEBP."
                );

                return;
            }


            /* Check file size */

            if (file.size > maxSize) {

                alert(
                    file.name +
                    " is larger than 5 MB.\n\n" +
                    "Maximum allowed size is 5 MB per image."
                );

                return;
            }


            validFiles.push(file);

        });


        /* =================================================
           NO VALID FILES
           ================================================= */

        if (validFiles.length === 0) {

            this.value = "";

            return;
        }


        /* =================================================
           SHOW IMAGE COUNT
           ================================================= */

        imageCount.textContent =
            validFiles.length +
            " image" +
            (validFiles.length > 1 ? "s" : "") +
            " selected";

        imageCount.style.display = "block";


        /* =================================================
           IMAGE PREVIEW
           ================================================= */

        validFiles.forEach(function (file, index) {

            const reader = new FileReader();

            reader.onload = function (event) {

                const column = document.createElement("div");

                column.className = "col-md-4 col-sm-6";


                column.innerHTML = `
                    <div class="card shadow-sm h-100">

                        <div
                            style="
                                height: 180px;
                                overflow: hidden;
                                position: relative;
                            "
                        >

                            <img
                                src="${event.target.result}"
                                alt="Property Image ${index + 1}"
                                style="
                                    width: 100%;
                                    height: 100%;
                                    object-fit: cover;
                                "
                            >

                            ${
                                index === 0
                                ? `
                                    <span
                                        class="badge bg-primary position-absolute top-0 start-0 m-2"
                                    >
                                        Main Image
                                    </span>
                                  `
                                : ""
                            }

                        </div>

                        <div class="card-body p-2">

                            <p
                                class="mb-1 text-truncate fw-semibold"
                                title="${file.name}"
                            >
                                ${file.name}
                            </p>

                            <small class="text-muted">
                                ${(file.size / (1024 * 1024)).toFixed(2)} MB
                            </small>

                        </div>

                    </div>
                `;


                imagePreviewContainer.appendChild(column);

            };


            reader.readAsDataURL(file);

        });

    });


    /* =====================================================
       FORM SUBMISSION VALIDATION
       ===================================================== */

    const propertyForm = propertyImages.closest("form");

    if (propertyForm) {

        propertyForm.addEventListener("submit", function (event) {

            const files = Array.from(propertyImages.files);


            /* No image */

            if (files.length === 0) {

                alert("Please select at least one property image.");

                event.preventDefault();

                return;
            }


            /* More than 5 */

            if (files.length > maxImages) {

                alert("You can upload a maximum of 5 images.");

                event.preventDefault();

                return;
            }


            /* Validate every image */

            for (const file of files) {

                if (!allowedTypes.includes(file.type)) {

                    alert(
                        file.name +
                        " is not a valid image format."
                    );

                    event.preventDefault();

                    return;
                }


                if (file.size > maxSize) {

                    alert(
                        file.name +
                        " is larger than 5 MB."
                    );

                    event.preventDefault();

                    return;
                }

            }


            /* Disable submit button */

            const submitButton =
                propertyForm.querySelector(
                    'button[type="submit"]'
                );

            if (submitButton) {

                submitButton.disabled = true;

                submitButton.textContent =
                    "Uploading Images...";

            }

        });

    }

});