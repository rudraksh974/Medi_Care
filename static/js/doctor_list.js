/**
 * Doctor List Page JavaScript
 * Handles tab switching between registered and external doctors
 */

(function() {
    'use strict';
  
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initDoctorList);
    } else {
      initDoctorList();
    }
  
    function initDoctorList() {
      const tabButtons = document.querySelectorAll('.tab-btn');
      const sections = {
        registered: document.getElementById('registered-section'),
        external: document.getElementById('external-section')
      };
  
      // Return early if elements don't exist
      if (tabButtons.length === 0 || !sections.registered || !sections.external) {
        return;
      }
  
      // Add click event listeners to tab buttons
      tabButtons.forEach(button => {
        button.addEventListener('click', function() {
          const tabName = this.getAttribute('data-tab');
          switchTab(tabName);
        });
      });
  
      /**
       * Switch between tabs
       * @param {string} tabName - The name of the tab to switch to
       */
      function switchTab(tabName) {
        // Update active button
        tabButtons.forEach(btn => {
          if (btn.getAttribute('data-tab') === tabName) {
            btn.classList.add('active');
            btn.setAttribute('aria-selected', 'true');
          } else {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
          }
        });
  
        // Update visible section
        Object.keys(sections).forEach(key => {
          if (key === tabName) {
            sections[key].classList.remove('hidden');
            sections[key].setAttribute('aria-hidden', 'false');
          } else {
            sections[key].classList.add('hidden');
            sections[key].setAttribute('aria-hidden', 'true');
          }
        });
  
        // Save preference to localStorage
        try {
          localStorage.setItem('doctorListActiveTab', tabName);
        } catch (e) {
          // localStorage might not be available
          console.warn('Could not save tab preference:', e);
        }
  
        // Smooth scroll to top of section
        const container = document.querySelector('.doctors-container');
        if (container) {
          const headerHeight = 100; // Approximate header height
          const targetPosition = container.offsetTop - headerHeight;
          
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
        }
      }
  
      /**
       * Restore previously selected tab from localStorage
       */
      function restoreSavedTab() {
        try {
          const savedTab = localStorage.getItem('doctorListActiveTab');
          if (savedTab && sections[savedTab]) {
            switchTab(savedTab);
          }
        } catch (e) {
          // localStorage might not be available
          console.warn('Could not restore tab preference:', e);
        }
      }
  
      // Restore saved tab on page load
      restoreSavedTab();
  
      // Add keyboard navigation
      tabButtons.forEach((button, index) => {
        button.addEventListener('keydown', function(e) {
          let newIndex;
  
          switch(e.key) {
            case 'ArrowLeft':
              e.preventDefault();
              newIndex = index > 0 ? index - 1 : tabButtons.length - 1;
              tabButtons[newIndex].focus();
              tabButtons[newIndex].click();
              break;
            
            case 'ArrowRight':
              e.preventDefault();
              newIndex = index < tabButtons.length - 1 ? index + 1 : 0;
              tabButtons[newIndex].focus();
              tabButtons[newIndex].click();
              break;
  
            case 'Home':
              e.preventDefault();
              tabButtons[0].focus();
              tabButtons[0].click();
              break;
  
            case 'End':
              e.preventDefault();
              tabButtons[tabButtons.length - 1].focus();
              tabButtons[tabButtons.length - 1].click();
              break;
          }
        });
      });
  
      // Add ARIA attributes for accessibility
      tabButtons.forEach(button => {
        button.setAttribute('role', 'tab');
        const isActive = button.classList.contains('active');
        button.setAttribute('aria-selected', isActive ? 'true' : 'false');
      });
  
      Object.values(sections).forEach(section => {
        section.setAttribute('role', 'tabpanel');
        const isHidden = section.classList.contains('hidden');
        section.setAttribute('aria-hidden', isHidden ? 'true' : 'false');
      });
  
      // Add animation to cards on scroll (optional enhancement)
      const observeCards = () => {
        const cards = document.querySelectorAll('.doctor-card');
        
        if ('IntersectionObserver' in window) {
          const cardObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
              if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                  entry.target.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                  entry.target.style.opacity = '1';
                  entry.target.style.transform = 'translateY(0)';
                }, 100);
                
                cardObserver.unobserve(entry.target);
              }
            });
          }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
          });
  
          cards.forEach(card => {
            cardObserver.observe(card);
          });
        }
      };
  
      // Observe cards initially and when tabs change
      observeCards();
      
      // Re-observe when switching tabs
      const originalSwitchTab = switchTab;
      switchTab = function(tabName) {
        originalSwitchTab(tabName);
        setTimeout(observeCards, 100);
      };
    }
  
    /**
     * Handle external links (open in new tab confirmation)
     */
    const externalLinks = document.querySelectorAll('a[target="_blank"]');
    externalLinks.forEach(link => {
      link.setAttribute('rel', 'noopener noreferrer');
    });
  
    /**
     * Add loading state to book appointment buttons
     */
    const bookButtons = document.querySelectorAll('.btn-book');
    bookButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        // Don't prevent default - let the link work
        // Just add a loading state
        this.style.opacity = '0.7';
        this.style.pointerEvents = 'none';
        
        const originalText = this.innerHTML;
        this.innerHTML = `
          <svg class="animate-spin" style="width: 18px; height: 18px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
          </svg>
          Loading...
        `;
        
        // Reset after navigation (in case user comes back)
        setTimeout(() => {
          this.innerHTML = originalText;
          this.style.opacity = '1';
          this.style.pointerEvents = 'auto';
        }, 3000);
      });
    });
  
    // Add CSS for spinning animation
    if (!document.querySelector('#doctor-list-animations')) {
      const style = document.createElement('style');
      style.id = 'doctor-list-animations';
      style.textContent = `
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `;
      document.head.appendChild(style);
    }
  
  })();