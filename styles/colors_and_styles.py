"""Color and style definitions module with palettes and CSS styles."""

# Define a list of base colors for the application
BASE_COLORS = [
    '#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
    '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'
] * 2  # Repeating the list to ensure enough unique colors if needed

# Define CSS styles for the application
CSS_STYLES = """
<style>
    /* Modern Typography System 2025 - CSS Variables */
    :root {
        /* Fluid Typography using clamp() for responsive sizing */
        --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
        --text-sm: clamp(0.875rem, 0.8rem + 0.375vw, 1rem);
        --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
        --text-lg: clamp(1.125rem, 1rem + 0.625vw, 1.5rem);
        --text-xl: clamp(1.5rem, 1.3rem + 1vw, 2rem);
        --text-2xl: clamp(2rem, 1.7rem + 1.5vw, 2.5rem);
        --text-3xl: clamp(2.5rem, 2rem + 2.5vw, 3.5rem);
        
        /* Line Heights - WCAG compliant */
        --leading-tight: 1.25;
        --leading-normal: 1.5;
        --leading-relaxed: 1.75;
        --leading-loose: 2;
        
        /* Font Weights */
        --font-normal: 400;
        --font-medium: 500;
        --font-semibold: 600;
        --font-bold: 700;
        --font-extrabold: 800;
        
        /* Variable Font with fallback stack */
        --font-family: 'Inter var', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* Support for variable fonts */
    @supports (font-variation-settings: normal) {
        :root {
            --font-family: 'Inter var', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
    }
    
    /* Base typography */
    body {
        font-family: var(--font-family);
        font-size: var(--text-base);
        line-height: var(--leading-normal);
        font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
    }
    
    .gradient-tile {
        transition: all 0.3s ease !important;
        color: #ffffff;
        font-family: var(--font-family);
    }
    
    .gradient-tile:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2) !important;
    }
    
    .gradient-tile h3 {
        font-size: var(--text-lg);
        line-height: var(--leading-tight);
        font-weight: var(--font-semibold);
        margin: 0;
    }
    
    .gradient-tile .tile-value {
        font-size: var(--text-2xl);
        line-height: var(--leading-tight);
        font-weight: var(--font-extrabold);
        margin: 0.5rem 0;
    }
    
    .gradient-tile .tile-label {
        font-size: var(--text-sm);
        line-height: var(--leading-normal);
        font-weight: var(--font-medium);
    }
    
    .tiles-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        padding: 1rem;
    }
    
    /* Accessibility: Respect user's motion preferences */
    @media (prefers-reduced-motion: reduce) {
        .gradient-tile {
            transition: none !important;
        }
        .gradient-tile:hover {
            transform: none !important;
        }
    }
    
    /* Ensure minimum touch target size (44x44px WCAG AAA) */
    .gradient-tile {
        min-height: 120px;
    }
</style>
"""
