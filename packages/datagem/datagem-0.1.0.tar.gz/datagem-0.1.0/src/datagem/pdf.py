#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:21:19 2025

Transformação de código API em um classe para construir um pacote.

@author: gilberto
"""

import re
import time
from google import genai
import random
import json
import os
from pandas import DataFrame

class DataExtractorPdf():
    """Extracts structured information from PDF files using the Gemini API.
    
        This class processes a folder of PDF files using structured prompts saved as text files.
        For each PDF, it sends one or more prompts to the Google Gemini API and formats the
        resulting JSON responses. For each prompt, a DataFrame is returned
        where each row corresponds to a PDF, and each column represents a
        field specified in the prompt.
    
        The prompts must be organized following the example in this directory: <incluir o prompt>.
    
        Parameters
        ----------
        api_key (str):
            Your API key for authentication with the Google GenAI service.
        model_name (str, optional):
            The name of the Gemini model to be used.
            Defaults to "gemini-2.5-flash-preview-05-20".
        path_files (str, optional):
            The path to the folder containing the PDF files to be processed.
            Defaults to ''.
        path_prompts (str, optional):
            The path to the folder containing the prompt files (.txt).
            Defaults to ''.
        shuffle (bool, optional):
            If True, the rows in DataFrame is shuffled.
            Default to False.
        random_state (int, optional):
            Seed to shuffle rows in DataFrame.
            Default to 42.
    
        Attributes
        ----------
        client_ : genai.Client
            The initialized Gemini API client.
        pdf_files_ : list[str]
            List of PDF filenames found in `path_files`.
            This attribute is created after the `fit()` method is called.
        prompt_files_ : list[str]
            List of prompt filenames found in `path_prompts`.
            This attribute is created after the `fit()` method is called.
        json_ : dict
            A dictionary where keys are the prompt filenames and values are lists
            of JSON responses (as strings) from the API. This attribute is
            populated by the `fit()` method.
    
        Example
        -------
        >>> from package.estimator import PdfExtractor
        >>> extractor = PdfExtractor(
        ...     api_key="YOUR_API_KEY",
        ...     path_files="path/to/my_pdfs/",
        ...     path_prompts="path/to/my_prompts/"
        ... )
        >>> extractor.fit()
        >>> results_df = extractor.transform()
        >>> print(results_df.head())
    """
    
    def __init__(self, api_key, model_name = "gemini-2.5-flash-preview-05-20", 
                 path_files = '', path_prompts = '', shuffle=False, random_state=42):
        self.api_key = api_key
        self.model_name = model_name
        self.path_files = path_files if path_files.endswith("/") else path_files + '/'
        self.path_prompts = path_prompts if path_prompts.endswith("/") else path_prompts + '/'
        self.shuffle = shuffle
        self.random_state = shuffle
        self.client_ = genai.Client(api_key=self.api_key)
    
    def __ask_ai(self, prompt, edital, max_tentativas=5):
        """
        Send a promtp to Gemini API with exponential backoff.

        Parameters
        ----------
        prompt : str
            A string (prompt) to sendo to gemini API.
        edital: str
            Pdf file to send to gemini.
        max_tentativas : int, optional
            Number of trials in the exponential backoff. The default is 5.

        Returns
        -------
        str
            A string with a markdown table.

        """    
        tentativa = 0
        file = self.client_.files.upload(file=self.path_files + edital)
        while tentativa < max_tentativas:
            try:
                resposta= self.client_.models.generate_content(
                   model=self.model_name,
                   contents=[prompt, file]
               )
                self.client_.files.delete(name=file.name)
                return resposta.text
            except:
                tentativa += 1
                tempo_espera = (2 ** tentativa) + random.random()
                print(f"Rate limite reached. Wait {tempo_espera:.2f} seconds.")
                time.sleep(tempo_espera)
        print("Maximum number of attempts reached.")
        return None

    def __make_prompt(self, file, question):
        """
        Generate a prompt using texts and a question.

        Parameters
        ----------
        file: str
            name of file in the computer
        question: str
            a question to be answered as a prompt

        Returns
        -------
        str
            string to be send to API gemini.

        """
        filename = self.path_prompts + question
        with open(filename, 'r') as f:
            prompt = f.read()
        return re.sub("<arquivo pdf>", file, prompt)    

    def extract_all(self,  verbose=True):
        """
        Call Gemini API to extract text using prompts.
        
        Parameters
        ----------------
        verbose: bool
            If True, every API invokation is printed.
            
        Returns
        -------
        dict
            key is prompt and value is a DataFrame
        
        """
 
        self.pdf_files_ = [file for file in os.listdir(self.path_files) if file.endswith('.pdf')]
        self.prompt_files_ = [file for file in os.listdir(self.path_prompts) if file.endswith('.txt')]
        self.json_ = {}
        
        # shuffle rows
        if self.shuffle:
            random.seed(self.random_state)
            self.pdf_files_ = random.shuffle(self.pdf_files_)
        
        for prompt_file in self.prompt_files_:
            json_files = []
            for pdf_file in self.pdf_files_:
                if verbose: 
                    print(f'{prompt_file=} | {pdf_file=}')
                prompt = self.__make_prompt(pdf_file,  prompt_file)
                answer = self.__ask_ai(prompt, pdf_file)
                answer = re.sub("```json", "", answer)
                answer = re.sub("```" , "", answer)
                answer = answer.strip()
                json_files.append(answer)
            self.json_[prompt_file] = json_files

        dict_df = {}
        
        for question in self.json_.keys():
            respostas = []
            for answer in self.json_[question]:
                dados_json = json.loads(answer)
                
                resposta = {}
                for key in dados_json.keys():
                    if isinstance(dados_json[key], list):
                        resposta[key] = ";".join([str(v) for v in dados_json[key]])
                    elif isinstance(dados_json[key], dict):
                        resposta[key] = ";".join([f'{k}:{v}' for k, v in dados_json[key].items()])
                    else:
                        resposta[key] = dados_json[key]
                respostas.append(resposta)
            dict_df[question] = DataFrame(respostas)
        return dict_df
    
    def extract_partial(self,  prompts, files = [], verbose=True):
        """
        Call Gemini API to extract text using prompts in prompts.
        
        Parameters
        ----------------
        verbose: bool
            If True, every API invokation is printed.
        prompts: list
            List of prompts in the path_prompts to extract information.
        files: list
            List of files in the path_files to extract information.
            Default to [], where all files will be analized.
            
        Returns
        -------
        dict
            key is prompt and value is a DataFrame
        
        """
        
        if files:
            self.pdf_files_ = files
        else: 
            self.pdf_files_ = [file for file in os.listdir(self.path_files) if file.endswith('.pdf')]
        self.prompt_files_ = prompts
        self.json_ = {}
        
        # shuffle rows
        if self.shuffle:
            random.seed(self.random_state)
            self.pdf_files_ = random.shuffle(self.pdf_files_)
        
        for prompt_file in self.prompt_files_:
            json_files = []
            for pdf_file in self.pdf_files_:
                if verbose: 
                    print(f'{prompt_file=} | {pdf_file=}')
                prompt = self.__make_prompt(pdf_file,  prompt_file)
                answer = self.__ask_ai(prompt, pdf_file)
                answer = re.sub("```json", "", answer)
                answer = re.sub("```" , "", answer)
                answer = answer.strip()
                json_files.append(answer)
            self.json_[prompt_file] = json_files

        dict_df = {}
        
        for question in self.json_.keys():
            respostas = []
            for answer in self.json_[question]:
                dados_json = json.loads(answer)
                
                resposta = {}
                for key in dados_json.keys():
                    if isinstance(dados_json[key], list):
                        resposta[key] = ";".join([str(v) for v in dados_json[key]])
                    elif isinstance(dados_json[key], dict):
                        resposta[key] = ";".join([f'{k}:{v}' for k, v in dados_json[key].items()])
                    else:
                        resposta[key] = dados_json[key]
                respostas.append(resposta)
            dict_df[question] = DataFrame(respostas)
        return dict_df
