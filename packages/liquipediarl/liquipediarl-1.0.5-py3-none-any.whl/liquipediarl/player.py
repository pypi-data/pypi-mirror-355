from bs4 import BeautifulSoup
from bs4.element import Tag

from typing import Optional

from . import constants

class Player():

    def __init__(self, _json: dict):
        self.name = _json['parse']['title']
        self.date = _json['curtimestamp']
        self.soup = BeautifulSoup(_json['parse']['text']['*'], 'html.parser')
        self.liquipedia = constants.BASE_PAGE_URL + self.name
        self.steam = None

    @staticmethod
    def get_all_players(region: str, _json: dict) -> dict:
        soup = BeautifulSoup(_json['parse']['text']['*'], 'html.parser')
        # Map row class to player status
        status_map = {
            'bg-neutral': 'Retired',
            'sapphire-bg': 'Inactive',
            'cinnabar-bg': 'Banned',
            'gigas-bg': 'Deceased'
        }
        # Extract records from a country table
        def parse_table(table: Tag, region: str, country: str) -> list:
            records = []
            # Find all records in the target table
            rows = table.find_all('tr')
            # Skip the header in the table and iterate through
            for row in rows[2:]:
                cols = row.find_all('td')
                if len(cols) < 4:  # Skip if column error
                    continue
                # Determine player status based on row CSS classes 
                # (e.g., 'Retired', 'Banned'); 'Active' if no match
                row_classes = row.get('class', [])
                status = next(
                    (status_map[c] for c in row_classes 
                        if c in status_map), 
                    'Active'  # Default
                )
                # Country image (Hosted by Liquipedia)
                country_img = cols[0].find('img')
                country_img = (constants.BASE_IMAGE_URL 
                                + country_img['src'] 
                                if country_img else '')
                # Player info
                player_name = cols[0].get_text(strip=True)
                real_name = cols[1].get_text(strip=True)
                player_page = cols[0].find('a', href=True)
                player_page = (constants.BASE_IMAGE_URL 
                                + player_page['href'] 
                                if player_page else '')
                # Team info
                team_name = cols[2].get_text(strip=True)
                team_img = cols[2].find('img')
                team_img = (constants.BASE_IMAGE_URL 
                            + team_img['src'] 
                            if team_img else '')
                # All links in one column
                external_links = cols[3].find_all('a', href=True)
                external_links = (', '.join(
                    [a['href'] for a in external_links]))
                # Append the results in the correct order
                records.append({
                    'name': player_name, 
                    'real': real_name, 
                    'status': status, 
                    'region': region, 
                    'country': country, 
                    'flag': country_img, 
                    'team': team_name, 
                    'teamlogo': team_img, 
                    'page': player_page, 
                    'links': external_links
                })
            return records

        # Parse each table to get all the players
        records = []
        for header in soup.find_all(['h3', 'h4']):
            # Check if header is a target table
            span = header.find('span', class_='mw-headline')
            if not span or not span.has_attr('id'):
                continue  # This header is not a target table
            # Get the country of the sepcified table
            country = span['id'].lstrip('_')
            # Go to the next table
            while header := header.find_next_sibling():
                # <h3><span id="Australia">Australia</span></h3>
                # <table> ... </table>  <- we're collecting this
                # <h3><span id="New_Zealand">New Zealand</span></h3>
                if header.name in ['h3', 'h4']:
                    break  # This isn't a table, go next
                if (header.name == 'table' 
                    and 'wikitable' in header.get('class', [])):
                    # Extract the records from the table and add to list
                    records.extend(
                        parse_table(header, region, country))
        return records

    def get_player_data(self) -> dict:
        data = {
            'info': self._get_info(),
            'image': self._get_image(),
            'links': self._get_links(),
            'steam': self._get_steam(),
            'liquipedia': self.liquipedia,
            'summary': self._get_summary(),
            'trivia': self._get_trivia(),
            'settings': self._get_settings(),
            'gallery': self._get_gallery()
        }
        return data

    def _get_info(self) -> dict:
        info = {'other': {}}
        # Find all key:value pairs in the infobox
        for label_div in self.soup.select('div.infobox-cell-2.infobox-description'):
            key = label_div.get_text(strip=True).strip(':').lower()
            value_div = label_div.find_next_sibling('div')
            if not value_div:
                continue
            value = value_div.get_text(' ', strip=True).replace('\xa0', ' ')
            # Handle known labels
            if 'name' in key:
                info['real'] = value
            elif 'nationality' in key:
                info['country'] = value
                flag = value_div.find('img')
                if flag:
                    info['flag'] = constants.BASE_IMAGE_URL + flag.get('src')
            elif 'born' in key:
                info['birthday'] = value
            elif 'region' in key:
                info['region'] = value
            elif 'status' in key:
                info['status'] = value
            elif 'role' in key:
                info['role'] = value
            elif 'years active' in key:
                info['active'] = value
            elif 'teams' in key:
                teams = [a.get_text(strip=True) 
                        for a in value_div.find_all('a')]
                info['teams'] = teams
            elif 'alternate ids' in key:
                info['aka'] = [x.strip() for x in value.split(',')]
            elif 'winnings' in key:
                info['earnings'] = value
            elif 'epic creator code' in key:
                info['creator_code'] = value
            elif 'starting game' in key:
                info['starting_game'] = value
            else:  # Catch any other labels we didn't explicitly get
                info['other'][key.replace(' ', '_')] = value
        return info
    
    def _get_image(self) -> Optional[str]:
        img_div = self.soup.find('div', class_='infobox-image')
        if not img_div:
            return None
        img = img_div.find('img')
        if not img or not img.get('src'):
            return None
        return constants.BASE_IMAGE_URL + img['src']

    def _get_links(self) -> list:
        links = []
        links_div = self.soup.find('div', class_='infobox-icons')
        if not links_div:
            return links
        for a in links_div.find_all('a', href=True):
            link = a['href']
            if link.startswith('https://steamcommunity.com'):
                self.steam = link
            else:
                links.append(link)
        return links
    
    def _get_steam(self) -> Optional[str]:
        if self.steam:
            return self.steam
        self._get_links()
        return self.steam

    def _get_summary(self) -> Optional[str]:
        for p in self.soup.find_all('p'):
            # Remove citation references like [1], [2], etc.
            for sup in p.find_all('sup'):
                sup.decompose()  # sups are biodegradable
            summary = p.get_text(' ', strip=True)
            if summary:
                return summary
        return None

    def _get_settings(self) -> dict:
        def parse_settings(table: Tag) -> dict:
            keys = [th.get_text(' ', strip=True).replace('\xa0', ' ') 
                       for th in table.find_all('th')]
            values = [td.get_text(' ', strip=True).replace('\xa0', ' ') 
                         for td in table.find_all('td')[:len(keys)]]
            return dict(zip(keys, values))
        def parse_controls(table: Tag) -> dict:
            keys = [th.get_text(' ', strip=True).replace('\xa0', ' ') 
                       for th in table.find_all('th')]
            values = []
            cols = table.find('tr').find_next_sibling('tr').find_all('td')
            for value in cols:
                img = value.find('img')
                alt = img.get('alt', '').strip('"') if img else ''
                src = img.get('src', '').strip('"') if img else ''
                url = constants.BASE_IMAGE_URL + src if src else ''
                values.append({'name': alt, 'image': url})
            return dict(zip(keys, values))
        def parse_hardware(table: Tag) -> dict:
            rows = table.find_all('tr')
            keys = [th.get_text(' ', strip=True).replace('\xa0', ' ')
                       for th in rows[0].find_all('th')]
            values = []
            cols = rows[1].find_all('td')
            for value in cols:
                hardware = value.get_text(' ', strip=True)
                img = value.find('img')
                src = img.get('src', '').strip('"') if img else ''
                url = constants.BASE_IMAGE_URL + src if src else ''
                values.append({'name': hardware, 'image': url})
            return dict(zip(keys, values))
        tables = self.soup.find_all('table')
        return {
            'camera': parse_settings(tables[0]) if len(tables) > 0 else {},
            'controls': parse_controls(tables[1]) if len(tables) > 1 else {},
            'deadzone': parse_settings(tables[2]) if len(tables) > 2 else {},
            'hardware': parse_hardware(tables[3]) if len(tables) > 3 else {}
        }

    def _get_achievements(self) -> None:
        # TODO
        pass

    def _get_results(self) -> None:
        # TODO
        pass

    def _get_trivia(self) -> list:
        trivia = []
        trivia_div = self.soup.find('span', id='Trivia')
        if not trivia_div:
            return trivia
        header = trivia_div.find_parent().find_next_sibling()
        while header and header.name != 'ul':
            header = header.find_next_sibling()
        if header and header.name == 'ul':
            for li in header.find_all('li'):
                # Remove citation references like [1], [2], etc.
                for sup in li.find_all('sup'):
                    sup.decompose()  # sups are biodegradable
                text = li.get_text(' ', strip=True).replace('\xa0', ' ')
                if text:
                    trivia.append(text)
        return trivia

    def _get_gallery(self) -> list:
        gallery = []
        for img in self.soup.find_all('img'):
            alt = img.get('alt', '').replace('\\"', '').strip('" ')
            # All gallery images alt text begins with the player's name
            if alt.startswith(self.name):
                src = img.get('src', '').replace('\\"', '').strip()
                url = constants.BASE_IMAGE_URL + src
                gallery.append({
                    'name': alt,
                    'image': url
                })
        return gallery
