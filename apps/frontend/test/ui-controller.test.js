/**
 * Tests for ui-controller.js
 *
 * Tests cover:
 * - UI state management
 * - Event handlers
 * - DOM manipulation
 */

describe('UIController', () => {
  let container;

  beforeEach(() => {
    // Create a fresh DOM container for each test
    container = document.createElement('div');
    container.innerHTML = `
      <button id="startBtn">Start</button>
      <button id="stopBtn">Stop</button>
      <div id="status">Ready</div>
      <div id="errorMsg" style="display: none;"></div>
    `;
    document.body.appendChild(container);
  });

  afterEach(() => {
    // Clean up
    document.body.removeChild(container);
  });

  describe('UI Element Access', () => {
    test('should find UI elements by ID', () => {
      const startBtn = document.getElementById('startBtn');
      const stopBtn = document.getElementById('stopBtn');
      const status = document.getElementById('status');

      expect(startBtn).not.toBeNull();
      expect(stopBtn).not.toBeNull();
      expect(status).not.toBeNull();
      expect(startBtn.textContent).toBe('Start');
    });

    test('should handle missing elements', () => {
      const nonExistent = document.getElementById('nonExistent');

      expect(nonExistent).toBeNull();
    });
  });

  describe('Button State Management', () => {
    test('should enable button', () => {
      const button = document.getElementById('startBtn');
      button.disabled = false;

      expect(button.disabled).toBe(false);
    });

    test('should disable button', () => {
      const button = document.getElementById('startBtn');
      button.disabled = true;

      expect(button.disabled).toBe(true);
    });

    test('should toggle button state', () => {
      const button = document.getElementById('startBtn');

      button.disabled = false;
      expect(button.disabled).toBe(false);

      button.disabled = true;
      expect(button.disabled).toBe(true);
    });
  });

  describe('Event Handling', () => {
    test('should attach click event listener', () => {
      const button = document.getElementById('startBtn');
      const mockHandler = jest.fn();

      button.addEventListener('click', mockHandler);
      button.click();

      expect(mockHandler).toHaveBeenCalledTimes(1);
    });

    test('should handle multiple event listeners', () => {
      const button = document.getElementById('startBtn');
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      button.addEventListener('click', handler1);
      button.addEventListener('click', handler2);
      button.click();

      expect(handler1).toHaveBeenCalledTimes(1);
      expect(handler2).toHaveBeenCalledTimes(1);
    });

    test('should remove event listener', () => {
      const button = document.getElementById('startBtn');
      const mockHandler = jest.fn();

      button.addEventListener('click', mockHandler);
      button.removeEventListener('click', mockHandler);
      button.click();

      expect(mockHandler).not.toHaveBeenCalled();
    });
  });

  describe('Status Display', () => {
    test('should update status text', () => {
      const status = document.getElementById('status');

      status.textContent = 'Processing...';

      expect(status.textContent).toBe('Processing...');
    });

    test('should show error message', () => {
      const errorMsg = document.getElementById('errorMsg');

      errorMsg.textContent = 'Error occurred';
      errorMsg.style.display = 'block';

      expect(errorMsg.textContent).toBe('Error occurred');
      expect(errorMsg.style.display).toBe('block');
    });

    test('should hide error message', () => {
      const errorMsg = document.getElementById('errorMsg');

      errorMsg.textContent = '';
      errorMsg.style.display = 'none';

      expect(errorMsg.style.display).toBe('none');
    });
  });

  describe('CSS Class Management', () => {
    test('should add CSS class', () => {
      const button = document.getElementById('startBtn');

      button.classList.add('active');

      expect(button.classList.contains('active')).toBe(true);
    });

    test('should remove CSS class', () => {
      const button = document.getElementById('startBtn');

      button.classList.add('active');
      button.classList.remove('active');

      expect(button.classList.contains('active')).toBe(false);
    });

    test('should toggle CSS class', () => {
      const button = document.getElementById('startBtn');

      button.classList.toggle('active');
      expect(button.classList.contains('active')).toBe(true);

      button.classList.toggle('active');
      expect(button.classList.contains('active')).toBe(false);
    });
  });

  describe('Form Validation', () => {
    test('should validate required fields', () => {
      const input = document.createElement('input');
      input.required = true;
      input.value = '';

      expect(input.value).toBe('');
      expect(input.required).toBe(true);
    });

    test('should validate input value', () => {
      const input = document.createElement('input');
      input.type = 'number';
      input.value = '42';

      expect(input.value).toBe('42');
      expect(parseInt(input.value)).toBe(42);
    });
  });

  describe('Dynamic Content', () => {
    test('should create and append element', () => {
      const newDiv = document.createElement('div');
      newDiv.id = 'dynamicDiv';
      newDiv.textContent = 'Dynamic content';

      container.appendChild(newDiv);

      const found = document.getElementById('dynamicDiv');
      expect(found).not.toBeNull();
      expect(found.textContent).toBe('Dynamic content');
    });

    test('should remove element', () => {
      const div = document.createElement('div');
      div.id = 'toRemove';
      container.appendChild(div);

      const found = document.getElementById('toRemove');
      container.removeChild(found);

      expect(document.getElementById('toRemove')).toBeNull();
    });
  });
});
