#!/usr/bin/env python3
"""
Citation DOI Finder

This script takes a text file with citations and finds DOIs for each citation. Outputs results to

Requirements:
pip install requests pandas openpyxl

Usage:
python3 doi_finder.py -i path/to/citations/list/ -o /path/to/csv/file/containing/dois               Add new dois to csv file
python3 doi_finder -c /path/to/csv/file                                                             Remove duplicate dois from csv file

Input format: one citation per line, any format

EX: 

Abate, A. R., and D. J. Durian, 2007, Phys. Rev. E 76, 021306.
Abou, B., and F. Gallet, 2004, Phys. Rev. Lett. 93, 160603.
...

Note: doi_finder.py will remove nonalphabetical characters at beginning of references, so having (1), [1], 1., etc at the beginning of citations should not affect performance. Nonalphabetical characters at the beginning of lines will not be saved.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import sys
import time
import re
import argparse
from crossref.restful import Works
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
from habanero import Crossref
import requests

class DOIFinder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({ 
            'User-Agent': 'DOI-Finder/1.0 (mailto:lucastro@umich.edu)' # Put your email here
        })
        
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.last_request_time = 0
    
    def rate_limit(self):
        """Implement rate limiting to be respectful to APIs"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()
    

    def find_doi(self, citation: str) -> Tuple[str, Optional[str], str]:
        """Find DOI for a single citation using crossref habanero api: https://github.com/sckott/habanero"""
        cr = Crossref()
        print(f"Searching for: {citation[:80]}...")
        try:  # Try CrossRef API (most comprehensive for academic papers)
            api_search_result = cr.works(query = citation)
            doi = api_search_result['message']['items'][0]['DOI']
            print(f"  Found DOI via CrossRef: {doi}")
            return citation, doi, "CrossRef"

        except:
            print(f'Failed to find doi for {citation[:80]}')
            return citation, 'Not Found', "CrossRef"
    
    def process_citations_file(self, file_path: str) -> List[Dict[str, str]]:
        """Process a file of citations and find DOIs"""
        with open(file_path, 'r', encoding='utf-8') as f:
            citations = [line.strip() for line in f if line.strip()]

        # Preprocess citations to remove non-alphabetical precursors
        for i in range(len(citations)):
            match = re.search(r'[a-zA-Z]', citations[i])
            if match:
                citations[i] = citations[i][match.start():].strip()

        print(f"Processing {len(citations)} citations...")
        
        results = []
        for i, citation in enumerate(citations, 1):
            print(f"\n[{i}/{len(citations)}]", end=" ")
            citation_text, doi, source = self.find_doi(citation)
            
            results.append({
                'citation': citation_text,
                'doi': doi if doi else '',
                'doi_url': f'https://doi.org/{doi}' if doi else '',
            })
            
            # Add a small delay between citations to not overload API
            if i < len(citations):
                time.sleep(0.5)
        
        return results
    
    def remove_duplicate_dois(self, results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate DOIs from results"""
        seen_dois = set()
        unique_results = []
        
        for result in results:
            if result['doi'] not in seen_dois:
                seen_dois.add(result['doi'])
                unique_results.append(result)
        
        return unique_results
    
    def save_results(self, results: List[Dict[str, str]], output_path: str, check_duplicates: bool):
        """Save results to Excel and CSV, preserving existing columns"""
        # Sanitize citations to remove invalid characters
        for result in results:
            result['citation'] = ''.join(c for c in result['citation'] if c.isprintable())

        new_df = pd.DataFrame(results)

        # Check if the Excel file already exists
        excel_path = output_path.replace('.csv', '.xlsx')
        if Path(excel_path).exists():
            try:
                # Load existing Excel file
                existing_df = pd.read_excel(excel_path)

                # Merge new results with existing data, preserving custom columns
                merged_df = pd.merge(existing_df, new_df, on='doi', how='outer', suffixes=('', '_new'))

                # Drop duplicate columns created during the merge
                for col in merged_df.columns:
                    if col.endswith('_new'):
                        merged_df[col.replace('_new', '')] = merged_df[col]
                        merged_df.drop(columns=[col], inplace=True)

                # Ensure new citations are added while preserving existing columns
                final_df = merged_df
            except Exception as e:
                print(f"Error loading existing Excel file: {e}")
                final_df = new_df
        else:
            final_df = new_df

        # Save as Excel
        try:
            final_df.to_excel(excel_path, index=False)
            print(f"\nResults saved to {excel_path}")
        except Exception as e:
            print(f"Error saving to Excel: {e}")

        # Save as CSV
        final_df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")

        # Print summary
        if not check_duplicates:
            found_count = len([r for r in results if r['doi'] != 'Not Found'])
            print(f"\nSummary:")
            print(f"Total citations: {len(results)}")
            print(f"DOIs found: {found_count}")
            print(f"Success rate: {found_count / len(results) * 100:.1f}%")

        else:
            initial_count = len(results)
            unique_results = self.remove_duplicate_dois(results)
            duplicates_removed = initial_count - len(unique_results)
            print(f"\nSummary:")
            print(f"Duplicate citations removed: {duplicates_removed}")
            print(f"Citations remaining after removal: {len(unique_results)}")


def main():
    parser = argparse.ArgumentParser(description='Find DOIs for citations')
    parser.add_argument('-i', '--input', required=False, help='Text file with citations (one per line)')
    parser.add_argument('-o', '--output', required=False, help='Output file path (default: dois.csv)', 
                        default='dois.csv')
    parser.add_argument('-c', '--clean', required=False, help='Clean a CSV file of duplicate DOIs')

    args = parser.parse_args()
    finder = DOIFinder()

    try:
        if args.clean:
            # Handle cleaning of duplicate DOIs in a CSV file
            csv_file = Path(args.clean)
            if not csv_file.exists():
                print(f"Error: CSV file not found: {csv_file}")
                sys.exit(1)

            print(f"Cleaning duplicate DOIs in {csv_file}...")
            existing_df = pd.read_csv(csv_file)
            existing_results = existing_df.to_dict('records')

            # Remove duplicate DOIs
            unique_results = finder.remove_duplicate_dois(existing_results)

            # Calculate statistics
            initial_count = len(existing_results)
            final_count = len(unique_results)
            duplicates_removed = initial_count - final_count

            # Save cleaned results back to the CSV file
            pd.DataFrame(unique_results).to_csv(csv_file, index=False)
            print(f"\nCleaned CSV file saved to {csv_file}")
            print(f"Summary:")
            print(f"Duplicate citations removed: {duplicates_removed}")
            print(f"Citations remaining after removal: {final_count}")

        elif args.input:
            # Handle citation processing with -i/-o flags
            citations_file = Path(args.input)
            if not citations_file.exists():
                print(f"Error: Citations file not found: {citations_file}")
                sys.exit(1)

            print(f"Processing citations from {citations_file}...")
            new_results = finder.process_citations_file(str(citations_file))

            # Load existing CSV file if it exists
            output_file = Path(args.output)
            
            if output_file.exists():
                print(f"Loading existing results from {output_file}...")
                existing_df = pd.read_csv(output_file)
                existing_results = existing_df.to_dict('records')

            else:
                existing_results = []

            # Combine new results with existing results, ensuring unique DOIs
            combined_results = existing_results + new_results
            unique_results = finder.remove_duplicate_dois(combined_results)

            # Calculate statistics
            total_existing = len(existing_results)
            total_new = len(new_results)
            total_combined = len(unique_results)
            duplicates_removed = (total_existing + total_new) - total_combined
            successfully_added = total_combined - total_existing

            # Save updated results
            finder.save_results(unique_results, args.output, check_duplicates=False)

            # Print summary
            print(f"\nSummary:")
            print(f"Total citations in CSV file: {total_combined}")
            print(f"New citations successfully added: {successfully_added}")
            print(f"Duplicate citations not added: {duplicates_removed}")

        else:
            print("Error: No valid arguments provided. Use -i for input file or -c for cleaning a CSV file.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()