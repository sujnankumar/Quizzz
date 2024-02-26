function addQuestion() {
    const container = document.getElementById('questions-container');
    const questionDiv = document.createElement('div');
    questionDiv.className = 'question';
    questionDiv.innerHTML = `
        <label>Question:</label>
        <input type="text" name="new_question_text[]">
        <button type="button" onclick="removeParentElement(this)">Remove Question</button>
        <div class="options-container">
            <!-- Placeholder for options; they will be added by addOption() -->
        </div>
        <button type="button" onclick="addOption(this.previousElementSibling)">Add Option</button>
    `;
    container.appendChild(questionDiv);
    // Automatically add one option field when adding a new question
    addOption(questionDiv.querySelector('.options-container'));
}

function addOption(container) {
    const optionDiv = document.createElement('div');
    optionDiv.className = 'option';
    const index = container.querySelectorAll('.option').length + 1;
    optionDiv.innerHTML = `
        <input type="text" name="new_option_text_${index}[]">
        <button type="button" onclick="removeParentElement(this)">Remove Option</button>
    `;
    container.appendChild(optionDiv); // Append the new option div to the options container
}

function removeParentElement(element) {
    element.parentNode.remove();
}
