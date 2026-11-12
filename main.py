from dataclasses import dataclass
from drafter import *

@dataclass
class AnalysisRecord:
    analysis_name: str
    filename: str
    img_description: str
    message_found: bool
    extracted_message: str
    
@dataclass
class State:
    uploaded_image: Picture
    filename: str
    analysis_name: str
    img_description: str
    save_to_history: bool
    latest_result: AnalysisRecord
    history: list[AnalysisRecord]
    
    
def extract_message(image: Picture) -> str:
    """Look for a supported hidden message in an image."""

    if image.width * image.height > 500000:
        return ""

    bits = ""

    for y in range(image.height):
        for x in range(image.width):
            pixel = image.get_pixel(x, y)

            bits += str(pixel[0] % 2)
            bits += str(pixel[1] % 2)
            bits += str(pixel[2] % 2)

    decoded_text = ""

    for i in range(0, len(bits) - 7, 8):
        byte = bits[i:i + 8]
        decoded_text += chr(int(byte, 2))

        if decoded_text.endswith("\0"):
            break

    if decoded_text.startswith("STEGO:") and "\0" in decoded_text:
        return decoded_text[6:decoded_text.index("\0")]

    return ""
    
@route
def index(state: State) -> Page:
    """Display the main homepage."""
    return home_page(state)
    
@route
def home_page(state: State) -> Page:
    """Display the homepage and main navigation options."""
    return Page(state, [
        "Welcome to Murray's Steganography Image Analyzer!",
        "Discover secret messages within images.",
        Button("Upload an Image", "upload_page"),
        Button("View Analysis History", "history_page")
    ])


@route
def upload_page(state: State) -> Page:
    """Display the image upload page."""
    return Page(state, [
        "Upload an Image",
        "Choose a PNG image from your computer.",
        "Important: Images must be 500,000 pixels or smaller.",
        "This analyzer looks for messages encoded using its supported STEGO format.",
        FileUpload("uploaded_image", accept=".png"),
        Button("Upload Image", "save_image"),
        Button("Back to Home", "home_page")
    ])


@route
def save_image(state: State,
               uploaded_image: Picture | None) -> Page:
    """Save the uploaded image to State."""

    if uploaded_image is None:
        return Page(state, [
            "No image was selected.",
            Button("Try Again", "upload_page")
        ])

    state.uploaded_image = uploaded_image
    state.filename = "Uploaded image"

    return confirmation_page(state)


@route
def confirmation_page(state: State) -> Page:
    """Confirm that the image was successfully uploaded."""
    return Page(state, [
        "Image Successfully Uploaded!",
        state.uploaded_image,
        "Your image is ready for analysis.",
        Button("Continue to Settings", "settings_page"),
        Button("Upload Another Image", "upload_page"),
        Button("Back to Home", "home_page")
    ])

@route
def settings_page(state: State) -> Page:
    """Display settings for the image analysis."""
    return Page(state, [
        "Analysis Settings",
        "Give this analysis a name:",
        TextBox("analysis_name", state.analysis_name),
        "Add a description of the image (optional):",
        TextArea("img_description", state.img_description),
        "Save this analysis to your history:",
        CheckBox("save_to_history", state.save_to_history),
        Button("Save Settings", "save_settings"),
        Button("Back to Home", "home_page")
    ])

@route
def save_settings(state: State,
                  analysis_name: str,
                  img_description: str,
                  save_to_history: bool) -> Page:
    """Save the user's analysis settings."""
    state.analysis_name = analysis_name
    state.img_description = img_description
    state.save_to_history = save_to_history

    return Page(state, [
        "Settings Saved!",
        "Analysis Name: " + state.analysis_name,
        "Description: " + state.img_description,
        "Save to History: " + str(state.save_to_history),
        Button("Continue to Analysis", "analyze_image"),
        Button("Back to Settings", "settings_page")
    ])

@route
def history_page(state: State) -> Page:
    """Display the user's previous analyses."""
    page_content = [
        "Analysis History",
        "Here are your previously saved analyses:"
    ]

    if len(state.history) == 0:
        page_content.append("You have no saved analyses yet.")

    for record in state.history:
        page_content.append("Analysis: " + record.analysis_name)
        page_content.append("Filename: " + record.filename)

        if record.message_found:
            page_content.append("Hidden message found!")
            page_content.append("Message: " + record.extracted_message)
        else:
            page_content.append("No supported hidden message detected.")

        page_content.append("--------------------")

    page_content.append(Button("Clear History", "clear_history"))
    page_content.append(Button("Back to Home", "home_page"))

    return Page(state, page_content)

@route
def clear_history(state: State) -> Page:
    """Clear all saved analysis records."""
    state.history = []

    return Page(state, [
        "Your analysis history has been cleared.",
        Button("View History", "history_page"),
        Button("Back to Home", "home_page")
    ])

@route
def analyze_image(state: State) -> Page:
    """Analyze the uploaded image for a supported hidden message."""
    if state.uploaded_image is None:
        return Page(state, [
            "No image is available to analyze.",
            Button("Upload an Image", "upload_page")
        ])

    extracted_message = extract_message(state.uploaded_image)
    message_found = extracted_message != ""

    if state.analysis_name == "":
        state.analysis_name = "Untitled Analysis"

    state.latest_result = AnalysisRecord(
        state.analysis_name,
        state.filename,
        state.img_description,
        message_found,
        extracted_message
    )

    if state.save_to_history:
        state.history.append(state.latest_result)

    return results_page(state)

@route
def results_page(state: State) -> Page:
    """Display the results of the image analysis."""
    if state.latest_result.message_found:
        result_text = "A supported hidden message was found!"
        message_text = state.latest_result.extracted_message
    else:
        result_text = "No supported hidden message was detected."
        message_text = "No message was extracted."

    return Page(state, [
        "Analysis Results",
        "Analysis Name: " + state.latest_result.analysis_name,
        "Image Description: " + state.latest_result.img_description,
        result_text,
        "Extracted Message:",
        message_text,
        Button("Analyze Another Image", "upload_page"),
        Button("View History", "history_page"),
        Button("Back to Home", "home_page")
    ])


start_server(State(None, "", "", "", False, None, []))
