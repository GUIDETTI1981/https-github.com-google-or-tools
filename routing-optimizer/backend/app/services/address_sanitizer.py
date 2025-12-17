"""
Address Sanitizer - Pulizia indirizzi italiani per geocoding

Questo modulo fornisce funzionalità per pulire e normalizzare indirizzi
provenienti da sistemi CRM, preparandoli per il geocoding accurato.

Autore: Senior Data Engineer & GIS Python Developer
Data: 2025-12-17
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AddressComponents:
    """
    Componenti di un indirizzo dopo la pulizia
    """
    street_type: Optional[str] = None  # Via, Viale, Corso, etc.
    street_name: Optional[str] = None  # Nome della via
    street_number: Optional[str] = None  # Numero civico
    city: Optional[str] = None  # Città
    province: Optional[str] = None  # Provincia (es. RM, MI)
    postal_code: Optional[str] = None  # CAP
    country: str = "Italia"  # Paese (default Italia)
    
    def to_string(self) -> str:
        """Ricostruisce l'indirizzo pulito come stringa"""
        parts = []
        
        if self.street_type and self.street_name:
            parts.append(f"{self.street_type} {self.street_name}")
        elif self.street_name:
            parts.append(self.street_name)
        
        if self.street_number:
            parts.append(self.street_number)
        
        if self.city:
            parts.append(self.city)
        
        if self.province:
            parts.append(f"({self.province})")
        
        if self.postal_code:
            parts.append(self.postal_code)
        
        return ", ".join(parts)


class AddressSanitizer:
    """
    Classe per pulire e normalizzare indirizzi italiani sporchi
    
    Features:
    - Normalizzazione abbreviazioni comuni (V. → Via, V.le → Viale)
    - Rimozione caratteri speciali inutili
    - Formattazione CAP (5 cifre)
    - Pulizia spazi multipli
    - Estrazione componenti indirizzo
    """
    
    # Mapping abbreviazioni comuni → forma completa
    STREET_TYPE_MAPPINGS = {
        # Via
        r'\bV\.\s*': 'Via ',
        r'\bv\.\s*': 'Via ',
        r'\bvia\b': 'Via',
        
        # Viale
        r'\bV\.le\s*': 'Viale ',
        r'\bVle\s*': 'Viale ',
        r'\bv\.le\s*': 'Viale ',
        r'\bvle\s*': 'Viale ',
        r'\bviale\b': 'Viale',
        
        # Corso
        r'\bC\.so\s*': 'Corso ',
        r'\bCso\s*': 'Corso ',
        r'\bc\.so\s*': 'Corso ',
        r'\bcso\s*': 'Corso ',
        r'\bcorso\b': 'Corso',
        
        # Piazza
        r'\bP\.za\s*': 'Piazza ',
        r'\bPza\s*': 'Piazza ',
        r'\bp\.za\s*': 'Piazza ',
        r'\bpza\s*': 'Piazza ',
        r'\bpiazza\b': 'Piazza',
        
        # Largo
        r'\bL\.go\s*': 'Largo ',
        r'\bLgo\s*': 'Largo ',
        r'\blargo\b': 'Largo',
        
        # Vicolo
        r'\bVic\.\s*': 'Vicolo ',
        r'\bvic\.\s*': 'Vicolo ',
        r'\bvicolo\b': 'Vicolo',
        
        # Strada
        r'\bStr\.\s*': 'Strada ',
        r'\bstr\.\s*': 'Strada ',
        r'\bstrada\b': 'Strada',
        
        # Contrada
        r'\bC\.da\s*': 'Contrada ',
        r'\bcda\s*': 'Contrada ',
        r'\bcontrada\b': 'Contrada',
        
        # Lungotevere
        r'\bL\.tevere\s*': 'Lungotevere ',
        r'\bltevere\s*': 'Lungotevere ',
        
        # Passaggio
        r'\bPass\.\s*': 'Passaggio ',
        r'\bpassaggio\b': 'Passaggio',
    }
    
    # Pattern CAP italiano (5 cifre)
    CAP_PATTERN = re.compile(r'\b(\d{5})\b')
    
    # Pattern numero civico (numero con possibili lettere/bis/ter)
    CIVIC_NUMBER_PATTERN = re.compile(r'\b(\d+\s*[A-Za-z]?(?:/\d+)?(?:\s*(?:bis|ter|quater))?)\b', re.IGNORECASE)
    
    # Pattern provincia (2 lettere maiuscole tra parentesi)
    PROVINCE_PATTERN = re.compile(r'\(([A-Z]{2})\)')
    
    # Caratteri da rimuovere (tranne quelli utili)
    CHARS_TO_REMOVE = r'[^\w\s,.\-/()\']'
    
    def __init__(self):
        """Inizializza l'address sanitizer"""
        logger.info("AddressSanitizer initialized")
    
    def clean(self, address: str) -> str:
        """
        Pulisce un indirizzo sporco
        
        Args:
            address: Indirizzo grezzo dal CRM
            
        Returns:
            Indirizzo pulito e normalizzato
            
        Example:
            >>> sanitizer = AddressSanitizer()
            >>> sanitizer.clean("v. roma  123/A - 00100  Roma (RM)")
            "Via Roma 123/A, Roma (RM), 00100"
        """
        if not address or not isinstance(address, str):
            return ""
        
        # Step 1: Converti in minuscolo per processing uniforme
        cleaned = address.strip()
        
        # Step 2: Rimuovi caratteri speciali inutili
        cleaned = re.sub(self.CHARS_TO_REMOVE, '', cleaned)
        
        # Step 3: Normalizza spazi multipli
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Step 4: Normalizza abbreviazioni tipi di strada
        for pattern, replacement in self.STREET_TYPE_MAPPINGS.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Step 5: Normalizza separatori (, ; - /)
        cleaned = re.sub(r'\s*[;/]\s*', ', ', cleaned)  # ; o / → ,
        cleaned = re.sub(r'\s+-\s+', ', ', cleaned)  # spazio-spazio → ,
        
        # Step 6: Rimuovi virgole multiple
        cleaned = re.sub(r',+', ',', cleaned)
        cleaned = re.sub(r',\s*,', ',', cleaned)
        
        # Step 7: Capitalizza correttamente
        cleaned = self._capitalize_properly(cleaned)
        
        # Step 8: Formatta CAP (se presente)
        cleaned = self._format_postal_code(cleaned)
        
        # Step 9: Cleanup finale
        cleaned = cleaned.strip().strip(',').strip()
        
        logger.debug(f"Address cleaned: '{address}' → '{cleaned}'")
        
        return cleaned
    
    def _capitalize_properly(self, text: str) -> str:
        """
        Capitalizza correttamente mantenendo acronimi e nomi propri
        
        Regole:
        - Prima lettera di ogni parola maiuscola
        - Parole dopo virgola: maiuscola
        - Preposizioni comuni: minuscolo (di, dei, della, dal, ecc.)
        """
        # Preposizioni da mantenere minuscole
        lowercase_words = {'di', 'dei', 'della', 'del', 'delle', 'degli', 'dal', 'dai', 'dalla', 'dalle'}
        
        words = text.split()
        result = []
        
        for i, word in enumerate(words):
            # Prima parola: sempre maiuscola
            if i == 0:
                result.append(word.capitalize())
            # Preposizioni: minuscole (eccetto dopo virgola)
            elif word.lower() in lowercase_words and not (i > 0 and words[i-1].endswith(',')):
                result.append(word.lower())
            # Province (RM, MI): mantieni maiuscole
            elif len(word) == 2 and word.isupper():
                result.append(word.upper())
            # Parole normali: capitalizza
            else:
                result.append(word.capitalize())
        
        return ' '.join(result)
    
    def _format_postal_code(self, text: str) -> str:
        """
        Formatta il CAP italiano (5 cifre)
        
        Esempi:
        - "100" → ignora (troppo corto)
        - "00100" → "00100" (già corretto)
        - "0100" → ignora (4 cifre non valido)
        - "001000" → ignora (6 cifre non valido)
        """
        # Trova tutti i CAP potenziali
        matches = self.CAP_PATTERN.findall(text)
        
        if matches:
            # Prendi il primo CAP valido trovato
            cap = matches[0]
            logger.debug(f"Found valid CAP: {cap}")
        
        return text
    
    def extract_components(self, address: str) -> AddressComponents:
        """
        Estrae i componenti di un indirizzo
        
        Args:
            address: Indirizzo pulito
            
        Returns:
            AddressComponents con componenti estratti
            
        Example:
            >>> sanitizer = AddressSanitizer()
            >>> components = sanitizer.extract_components("Via Roma 123/A, Milano (MI), 20100")
            >>> components.street_type
            "Via"
            >>> components.street_name
            "Roma"
            >>> components.street_number
            "123/A"
        """
        components = AddressComponents()
        
        # Pulisci l'indirizzo prima dell'estrazione
        cleaned = self.clean(address)
        
        # Estrai CAP
        cap_match = self.CAP_PATTERN.search(cleaned)
        if cap_match:
            components.postal_code = cap_match.group(1)
            # Rimuovi CAP dall'indirizzo per facilitare altre estrazioni
            cleaned = cleaned.replace(cap_match.group(0), '').strip()
        
        # Estrai provincia
        province_match = self.PROVINCE_PATTERN.search(cleaned)
        if province_match:
            components.province = province_match.group(1)
            # Rimuovi provincia
            cleaned = self.PROVINCE_PATTERN.sub('', cleaned).strip()
        
        # Split per virgole
        parts = [p.strip() for p in cleaned.split(',') if p.strip()]
        
        if len(parts) >= 2:
            # Prima parte: via e numero
            street_part = parts[0]
            
            # Estrai tipo di strada
            for pattern, street_type in self.STREET_TYPE_MAPPINGS.items():
                if re.match(pattern, street_part, re.IGNORECASE):
                    components.street_type = street_type.strip()
                    street_part = re.sub(pattern, '', street_part, flags=re.IGNORECASE).strip()
                    break
            
            # Estrai numero civico
            civic_match = self.CIVIC_NUMBER_PATTERN.search(street_part)
            if civic_match:
                components.street_number = civic_match.group(1)
                components.street_name = street_part.replace(civic_match.group(0), '').strip()
            else:
                components.street_name = street_part
            
            # Seconda parte: città
            components.city = parts[1]
        
        elif len(parts) == 1:
            # Solo una parte: considera come via completa
            components.street_name = parts[0]
        
        logger.debug(f"Address components extracted: {components}")
        
        return components
    
    def validate_address(self, address: str) -> bool:
        """
        Valida se un indirizzo è minimamente completo per il geocoding
        
        Un indirizzo valido deve avere:
        - Almeno 5 caratteri
        - Almeno una parola significativa
        
        Args:
            address: Indirizzo da validare
            
        Returns:
            True se valido, False altrimenti
        """
        if not address or not isinstance(address, str):
            return False
        
        cleaned = self.clean(address)
        
        # Troppo corto
        if len(cleaned) < 5:
            return False
        
        # Deve avere almeno una parola significativa (non solo numeri/punteggiatura)
        words = re.findall(r'\b[a-zA-Z]+\b', cleaned)
        if len(words) < 1:
            return False
        
        return True
    
    def get_info(self) -> dict:
        """
        Ottiene informazioni sul sanitizer
        
        Returns:
            Dict con configurazione e statistiche
        """
        return {
            "street_type_mappings_count": len(self.STREET_TYPE_MAPPINGS),
            "supported_abbreviations": list(self.STREET_TYPE_MAPPINGS.keys())[:10],  # Prime 10
            "features": [
                "Normalizzazione abbreviazioni",
                "Rimozione caratteri speciali",
                "Formattazione CAP",
                "Capitalizzazione corretta",
                "Estrazione componenti",
                "Validazione indirizzo"
            ]
        }


# Singleton instance (opzionale)
_address_sanitizer_instance: Optional[AddressSanitizer] = None


def get_address_sanitizer() -> AddressSanitizer:
    """
    Factory function per ottenere un'istanza singleton del sanitizer
    
    Returns:
        AddressSanitizer instance
    """
    global _address_sanitizer_instance
    
    if _address_sanitizer_instance is None:
        _address_sanitizer_instance = AddressSanitizer()
    
    return _address_sanitizer_instance
