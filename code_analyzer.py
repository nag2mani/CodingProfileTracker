# backend/app/services/code_analyzer.py
import google.generativeai as genai
from flask import current_app
import re

class CodeAnalyzer:
    def __init__(self):  # Fixed typo: _init_ to __init__
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_code(self, code_data):
        prompt = self._create_analysis_prompt(code_data)
        
        try:
            response = self.model.generate_content(prompt)
            return self.parse_analysis(response.text)
        except Exception as e:
            current_app.logger.error(f"Analysis failed: {str(e)}")
            raise

    def _create_analysis_prompt(self, code_data):
        return f"""
        Analyze this code solution for the following DSA problem:

        Problem Title: {code_data.get('question_title')}
        Problem Description: {code_data.get('question_description')}

        Code ({code_data.get('language')}):
        {code_data.get('code')}

        Provide a detailed analysis in the following format:

        1. COMPLEXITY ANALYSIS
        - Time Complexity
        - Space Complexity
        - Explanation of the complexity

        2. OPTIMIZATION SUGGESTIONS
        - List specific ways to improve the solution
        - Alternative approaches

        3. CODE QUALITY
        - Code structure
        - Variable naming
        - Readability

        4. BEST PRACTICES
        - DSA-specific recommendations
        - Language-specific improvements
        """

    def parse_analysis(self, analysis_text):
        sections = {
            'complexity_analysis': self._extract_section(analysis_text, 'COMPLEXITY ANALYSIS'),
            'optimization_suggestions': self._extract_section(analysis_text, 'OPTIMIZATION SUGGESTIONS'),
            'code_quality': self._extract_section(analysis_text, 'CODE QUALITY'),
            'best_practices': self._extract_section(analysis_text, 'BEST PRACTICES')
        }
        return sections

    def _extract_section(self, text, section_name):
        pattern = rf"{section_name}(.*?)(?=\d\.|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            points = [point.strip('- ').strip() 
                     for point in content.split('\n') 
                     if point.strip()]
            return {
                'details': points,
                'summary': points[0] if points else "No analysis available"
            }
        return {"details": [], "summary": "Section not found"}