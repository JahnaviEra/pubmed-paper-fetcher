import time
import logging
import pandas as pd
import requests
from xml.etree import ElementTree as ET
from typing import List, Dict
from multiprocessing import Pool

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedFetcher:
    """
    A class to fetch and parse information from the PubMed database using the NCBI E-utilities API.

    This class provides methods to fetch paper IDs based on search terms,
    fetch paper details using PubMed IDs, and parse the XML response from the API.
    """

    def __init__(self, email: str):
        """
        Initializes the PubMedFetcher with the provided email.
        """
        self.email = email

    def fetch_paper_ids(self, search_term: str, max_results: int = 10) -> List[str]:
        """
        Fetches a list of PubMed paper IDs based on the provided search term.

        Args:
            search_term (str): The search term to query PubMed.
            max_results (int, optional): The maximum number of results to return. Defaults to 10.

        Returns:
            List[str]: A list of PubMed IDs that match the search term.
        """
        logging.info(
            f"Fetching paper IDs for search term: {search_term} with max results: {max_results}"
        )
        url = f"{BASE_URL}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": search_term,
            "retmax": max_results,
            "retmode": "json",
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])

    def fetch_paper_details(self, pubmed_id: str) -> Dict[str, str]:
        """
        Fetches detailed information for a specific PubMed paper given its PubMed ID.

        Args:
            pubmed_id (str): The PubMed ID of the paper to fetch details for.

        Returns:
            Dict[str, str]: A dictionary containing details such as PubMed ID, title, and publication date.
        """
        logging.info(f"Fetching details for PubMed ID: {pubmed_id}")
        url = f"{BASE_URL}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": pubmed_id,
            "retmode": "xml",
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        time.sleep(2)  # Adding delay to avoid hitting rate limits
        return self.parse_paper_details(response.text)

    def parse_paper_details(self, xml_data: str) -> Dict[str, str]:
        """
        Parses the XML data returned by the PubMed API to extract relevant paper details.

        Args:
            xml_data (str): The XML response from the PubMed API.

        Returns:
            Dict[str, str]: A dictionary containing parsed details such as PubMed ID, title, and publication date.
        """
        root = ET.fromstring(xml_data)

        # Extract PubMed ID
        pubmed_id = (
            root.find(".//PMID").text if root.find(".//PMID") is not None else "N/A"
        )

        # Extract Title
        title = (
            root.find(".//ArticleTitle").text
            if root.find(".//ArticleTitle") is not None
            else "N/A"
        )

        # Extract Publication Date
        pub_date_elem = root.find(".//DateCompleted")
        publication_date = "N/A"
        if pub_date_elem:
            year = (
                pub_date_elem.find("Year").text
                if pub_date_elem.find("Year") is not None
                else "N/A"
            )
            month = (
                pub_date_elem.find("Month").text
                if pub_date_elem.find("Month") is not None
                else "N/A"
            )
            day = (
                pub_date_elem.find("Day").text
                if pub_date_elem.find("Day") is not None
                else "N/A"
            )
            publication_date = f"{year}-{month}-{day}"

        # Extract Author Information
        authors = []
        non_academic_authors = []
        company_affiliations = set()
        corresponding_author_email = None

        for author in root.findall(".//Author"):
            last_name = (
                author.find("LastName").text
                if author.find("LastName") is not None
                else "N/A"
            )
            fore_name = (
                author.find("ForeName").text
                if author.find("ForeName") is not None
                else "N/A"
            )
            affiliation = (
                author.find(".//Affiliation").text
                if author.find(".//Affiliation") is not None
                else "N/A"
            )
            email = None
            if affiliation:
                # Check for email in affiliation
                email = next(
                    (word for word in affiliation.split() if "@" in word), None
                )

            # Construct the author name
            author_name = f"{fore_name} {last_name}"

            # Categorize non-academic authors and companies
            if email:
                corresponding_author_email = (
                    email
                    if not corresponding_author_email
                    else corresponding_author_email
                )
            if not self.is_academic(affiliation):
                non_academic_authors.append(author_name)
            if self.is_company(affiliation):
                # Add the company affiliation only if it's not already in the set
                company_affiliations.add(affiliation)

        return {
            "PubmedID": pubmed_id,
            "Title": title,
            "Publication Date": publication_date,
            "Non-academic Author(s)": (
                "; ".join(non_academic_authors) if non_academic_authors else "None"
            ),
            "Company Affiliation(s)": (
                "; ".join(company_affiliations) if company_affiliations else "None"
            ),
            "Corresponding Author Email": (
                corresponding_author_email if corresponding_author_email else "None"
            ),
        }

    def is_academic(self, affiliation: str) -> bool:
        """
        Determines if the affiliation is academic.

        Args:
            affiliation (str): The affiliation of the author.

        Returns:
            bool: True if the affiliation is academic, False otherwise.
        """
        academic_keywords = [
            "University",
            "Institute",
            "College",
            "Research",
            "Academy",
        ]
        return any(keyword in affiliation for keyword in academic_keywords)

    def is_company(self, affiliation: str) -> bool:
        """
        Determines if the affiliation is a company.

        Args:
            affiliation (str): The affiliation of the author.

        Returns:
            bool: True if the affiliation is a company, False otherwise.
        """
        company_keywords = ["Pharma", "Biotech", "Pharmaceutical", "Biotechnology"]
        return any(keyword in affiliation for keyword in company_keywords)


def write_csv(filename: str, data: List[Dict[str, str]]) -> None:
    """
    Writes the fetched paper details to a CSV file.

    Args:
        filename (str): The name of the CSV file to write the data to.
        data (List[Dict[str, str]]): A list of dictionaries containing paper details.
    """
    logging.info(f"Writing data to CSV file: {filename}")
    df = pd.DataFrame(data)
    df.to_csv(
        filename, mode="a", header=not pd.io.common.file_exists(filename), index=False
    )


def fetch_details_concurrently(
    pubmed_ids: List[str], fetcher: PubMedFetcher
) -> List[Dict[str, str]]:
    """
    Fetches paper details concurrently using multiprocessing.

    Args:
        pubmed_ids (List[str]): A list of PubMed IDs to fetch details for.
        fetcher (PubMedFetcher): An instance of the PubMedFetcher class used to fetch paper details.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the details of each paper.
    """
    logging.info(
        f"Using multiprocessing to fetch details for {len(pubmed_ids)} PubMed IDs"
    )
    with Pool(processes=2) as pool:
        results = pool.map(fetcher.fetch_paper_details, pubmed_ids)
    return results
