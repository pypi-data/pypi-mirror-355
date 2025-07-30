class AutocompleteInput extends HTMLElement {
    static formAssociated = true;
    
    constructor() {
        super();
        this.debounceTimeout = null;
        this.debounceDelay = 300;
        this.minLength = 2;
        this.activeIndex = -1;
        this.results = [];
        
        this._internals = this.attachInternals();
        
        this.input = this.shadowRoot.querySelector('input');
        this.resultsContainer = this.shadowRoot.querySelector('.results');
        
        this.setupAccessibility();
        this.setupEventListeners();
    }
    
    setupAccessibility() {
        // Generate unique IDs for ARIA relationships
        this.inputId = `autocomplete-input-${Math.random().toString(36).substr(2, 9)}`;
        this.listboxId = `autocomplete-listbox-${Math.random().toString(36).substr(2, 9)}`;
        
        // Set ARIA attributes on input
        this.input.setAttribute('id', this.inputId);
        this.input.setAttribute('role', 'combobox');
        this.input.setAttribute('aria-autocomplete', 'list');
        this.input.setAttribute('aria-expanded', 'false');
        this.input.setAttribute('aria-controls', this.listboxId);
        this.input.setAttribute('aria-haspopup', 'listbox');
        
        // Set ARIA attributes on results container
        this.resultsContainer.setAttribute('id', this.listboxId);
        this.resultsContainer.setAttribute('role', 'listbox');
        this.resultsContainer.setAttribute('aria-label', 'Autocomplete suggestions');
    }
    
    setupEventListeners() {
        this.input.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
            this.updateFormValue(e.target.value);
        });
        
        this.input.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });
        
        this.input.addEventListener('focus', () => {
            if (this.input.value.length >= this.minLength) {
                this.showResults();
            }
        });
        
        this.input.addEventListener('blur', (e) => {
            // Don't hide if clicking on a result item
            if (e.relatedTarget && this.resultsContainer.contains(e.relatedTarget)) {
                return;
            }
            setTimeout(() => this.hideResults(), 150);
        });
        
        document.addEventListener('click', (e) => {
            if (!this.contains(e.target)) {
                this.hideResults();
            }
        });
    }
    
    handleInput(value) {
        clearTimeout(this.debounceTimeout);
        
        if (value.length < this.minLength) {
            this.hideResults();
            return;
        }
        
        this.debounceTimeout = setTimeout(() => {
            this.fetchResults(value);
        }, this.debounceDelay);
    }
    
    async fetchResults(query) {
        const endpoint = this.getAttribute('endpoint');
        if (!endpoint) {
            console.error('No endpoint attribute specified');
            return;
        }
        
        try {
            this.showLoading();
            
            const url = new URL(endpoint, window.location.origin);
            url.searchParams.append('q', query);
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.renderResults(data.results || []);
            
        } catch (error) {
            console.error('Fetch error:', error);
            this.showError('Failed to fetch results');
        }
    }
    
    showLoading() {
        this.resultsContainer.innerHTML = '<div class="loading" role="status" aria-live="polite">Loading...</div>';
        this.showResults();
    }
    
    showError(message) {
        this.resultsContainer.innerHTML = `<div class="loading" role="alert">${message}</div>`;
        this.showResults();
    }
    
    renderResults(results) {
        this.results = results;
        this.activeIndex = -1;
        
        if (results.length === 0) {
            this.resultsContainer.innerHTML = '<div class="loading" role="status" aria-live="polite">No results found</div>';
            this.showResults();
            return;
        }
        
        const html = results.map((result, index) => {
            const displayText = typeof result === 'string' ? result : result.name || result.title || result.text || JSON.stringify(result);
            const optionId = `${this.listboxId}-option-${index}`;
            return `<div class="result-item" 
                         role="option" 
                         id="${optionId}" 
                         data-value="${displayText}" 
                         data-index="${index}"
                         tabindex="-1"
                         aria-selected="false">${displayText}</div>`;
        }).join('');
        
        this.resultsContainer.innerHTML = html;
        
        this.resultsContainer.querySelectorAll('.result-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectResult(item.dataset.value);
            });
        });
        
        this.showResults();
    }
    
    selectResult(value) {
        this.input.value = value;
        this.updateFormValue(value);
        this.hideResults();
        
        this.dispatchEvent(new CustomEvent('autocomplete-select', {
            detail: { value },
            bubbles: true
        }));
    }
    
    updateFormValue(value) {
        this._internals.setFormValue(value);
    }
    
    get name() {
        return this.getAttribute('name');
    }
    
    get value() {
        return this.input.value;
    }
    
    set value(val) {
        this.input.value = val;
        this.updateFormValue(val);
    }
    
    handleKeyDown(e) {
        const isResultsVisible = this.resultsContainer.style.display === 'block';
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (!isResultsVisible && this.input.value.length >= this.minLength) {
                    this.fetchResults(this.input.value);
                } else if (this.results.length > 0) {
                    this.moveActiveIndex(1);
                }
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                if (this.results.length > 0) {
                    this.moveActiveIndex(-1);
                }
                break;
                
            case 'Enter':
                if (isResultsVisible && this.activeIndex >= 0) {
                    e.preventDefault();
                    this.selectActiveResult();
                }
                break;
                
            case 'Escape':
                if (isResultsVisible) {
                    e.preventDefault();
                    this.hideResults();
                    this.input.focus();
                }
                break;
                
            case 'Tab':
                if (isResultsVisible) {
                    this.hideResults();
                }
                break;
        }
    }
    
    moveActiveIndex(direction) {
        const maxIndex = this.results.length - 1;
        
        if (direction > 0) {
            this.activeIndex = this.activeIndex < maxIndex ? this.activeIndex + 1 : 0;
        } else {
            this.activeIndex = this.activeIndex > 0 ? this.activeIndex - 1 : maxIndex;
        }
        
        this.updateActiveDescendant();
    }
    
    updateActiveDescendant() {
        // Clear previous selection
        this.resultsContainer.querySelectorAll('.result-item').forEach(item => {
            item.setAttribute('aria-selected', 'false');
            item.classList.remove('active');
        });
        
        if (this.activeIndex >= 0) {
            const activeItem = this.resultsContainer.querySelector(`[data-index="${this.activeIndex}"]`);
            if (activeItem) {
                activeItem.setAttribute('aria-selected', 'true');
                activeItem.classList.add('active');
                this.input.setAttribute('aria-activedescendant', activeItem.id);
                
                // Scroll into view if needed
                activeItem.scrollIntoView({ block: 'nearest' });
            }
        } else {
            this.input.removeAttribute('aria-activedescendant');
        }
    }
    
    selectActiveResult() {
        if (this.activeIndex >= 0 && this.results[this.activeIndex]) {
            const value = typeof this.results[this.activeIndex] === 'string' 
                ? this.results[this.activeIndex] 
                : this.results[this.activeIndex].name || this.results[this.activeIndex].title || this.results[this.activeIndex].text;
            this.selectResult(value);
        }
    }
    
    showResults() {
        this.resultsContainer.style.display = 'block';
        this.input.setAttribute('aria-expanded', 'true');
    }
    
    hideResults() {
        this.resultsContainer.style.display = 'none';
        this.input.setAttribute('aria-expanded', 'false');
        this.input.removeAttribute('aria-activedescendant');
        this.activeIndex = -1;
    }
}

customElements.define('autocomplete-input', AutocompleteInput);